"""
Mathematical Expression Parser for CellSorter (TASK-020)

Safe expression parsing and evaluation system for advanced cell selection filtering.
Supports mathematical expressions, statistical functions, and logical operations.

Examples:
    'area > mean(area) + 2*std(area)'
    'aspect_ratio < 1.5 AND intensity > percentile(intensity, 75)'
    'circularity > 0.8 OR area > 1000'
    'NOT (intensity < 100 OR area < 50)'
"""

import ast
import operator
import re
from typing import Dict, Any, List, Union, Optional, Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from utils.logging_config import LoggerMixin


class ExpressionError(Exception):
    """Base exception for expression parsing and evaluation errors."""
    pass


class ParseError(ExpressionError):
    """Exception raised when expression cannot be parsed."""
    pass


class EvaluationError(ExpressionError):
    """Exception raised when expression cannot be evaluated."""
    pass


class SecurityError(ExpressionError):
    """Exception raised when expression contains unsafe operations."""
    pass


class ExpressionType(Enum):
    """Types of expression results."""
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    ARRAY = "array"


@dataclass
class ExpressionResult:
    """Result of expression evaluation."""
    value: Union[bool, float, np.ndarray]
    expression_type: ExpressionType
    column_dependencies: List[str]
    execution_time: float
    error_message: Optional[str] = None


class StatisticalFunctions:
    """Statistical functions available in expressions."""
    
    @staticmethod
    def mean(data: np.ndarray) -> float:
        """Calculate mean of data array."""
        return float(np.nanmean(data))
    
    @staticmethod
    def std(data: np.ndarray) -> float:
        """Calculate standard deviation of data array."""
        return float(np.nanstd(data))
    
    @staticmethod
    def var(data: np.ndarray) -> float:
        """Calculate variance of data array."""
        return float(np.nanvar(data))
    
    @staticmethod
    def min(data: np.ndarray) -> float:
        """Calculate minimum of data array."""
        return float(np.nanmin(data))
    
    @staticmethod
    def max(data: np.ndarray) -> float:
        """Calculate maximum of data array."""
        return float(np.nanmax(data))
    
    @staticmethod
    def median(data: np.ndarray) -> float:
        """Calculate median of data array."""
        return float(np.nanmedian(data))
    
    @staticmethod
    def percentile(data: np.ndarray, q: float) -> float:
        """Calculate percentile of data array."""
        if not 0 <= q <= 100:
            raise ValueError("Percentile must be between 0 and 100")
        return float(np.nanpercentile(data, q))
    
    @staticmethod
    def count(data: np.ndarray) -> float:
        """Count non-NaN values in data array."""
        return float(np.sum(~np.isnan(data)))
    
    @staticmethod
    def sum(data: np.ndarray) -> float:
        """Calculate sum of data array."""
        return float(np.nansum(data))
    
    @staticmethod
    def abs(data: np.ndarray) -> np.ndarray:
        """Calculate absolute value of data array."""
        return np.abs(data)
    
    @staticmethod
    def sqrt(data: np.ndarray) -> np.ndarray:
        """Calculate square root of data array."""
        return np.sqrt(np.maximum(data, 0))  # Avoid negative sqrt
    
    @staticmethod
    def log(data: np.ndarray) -> np.ndarray:
        """Calculate natural logarithm of data array."""
        return np.log(np.maximum(data, 1e-10))  # Avoid log(0)
    
    @staticmethod
    def log10(data: np.ndarray) -> np.ndarray:
        """Calculate base-10 logarithm of data array."""
        return np.log10(np.maximum(data, 1e-10))  # Avoid log10(0)

class ExpressionParser(LoggerMixin):
    """
    Safe mathematical expression parser using AST.
    
    Features:
    - Safe evaluation using AST visitor pattern
    - Support for mathematical and logical operations
    - Statistical functions (mean, std, percentile, etc.)
    - Column variable support
    - Vectorized operations for performance
    """
    
    # Allowed operators
    BINARY_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.FloorDiv: operator.floordiv,
    }
    
    COMPARISON_OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda x, y: np.isin(x, y),
        ast.NotIn: lambda x, y: ~np.isin(x, y),
    }
    
    BOOLEAN_OPERATORS = {
        ast.And: np.logical_and,
        ast.Or: np.logical_or,
    }
    
    UNARY_OPERATORS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: np.logical_not,
    }
    
    def __init__(self):
        super().__init__()
        self.statistical_functions = StatisticalFunctions()
        self.variables: Dict[str, np.ndarray] = {}
        self.column_dependencies: List[str] = []
        
    def parse_expression(self, expression: str) -> ast.AST:
        """
        Parse expression string into AST.
        
        Args:
            expression: Mathematical expression string
            
        Returns:
            Parsed AST tree
            
        Raises:
            ParseError: If expression cannot be parsed
        """
        try:
            # Clean and normalize expression
            expression = self._normalize_expression(expression)
            
            # Parse into AST
            tree = ast.parse(expression, mode='eval')
            
            # Validate AST for security
            self._validate_ast(tree)
            
            return tree
            
        except SyntaxError as e:
            raise ParseError(f"Invalid expression syntax: {e}")
        except Exception as e:
            raise ParseError(f"Failed to parse expression: {e}")
    
    def evaluate_expression(self, expression: str, data: pd.DataFrame) -> ExpressionResult:
        """
        Evaluate mathematical expression against DataFrame.
        
        Args:
            expression: Mathematical expression string
            data: DataFrame with column data
            
        Returns:
            ExpressionResult with evaluation results
        """
        import time
        start_time = time.time()
        
        try:
            # Reset state
            self.variables = {}
            self.column_dependencies = []
            
            # Parse expression
            tree = self.parse_expression(expression)
            
            # Set up variables from DataFrame columns
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            for column in numeric_columns:
                self.variables[column] = data[column].values
            
            # Evaluate AST
            result = self._evaluate_node(tree.body)
            
            # Determine result type
            if isinstance(result, np.ndarray):
                if result.dtype == bool:
                    expr_type = ExpressionType.BOOLEAN
                else:
                    expr_type = ExpressionType.ARRAY
            elif isinstance(result, (bool, np.bool_)):
                expr_type = ExpressionType.BOOLEAN
            else:
                expr_type = ExpressionType.NUMERIC
            
            execution_time = time.time() - start_time
            
            self.log_info(f"Expression evaluated successfully in {execution_time:.3f}s")
            
            return ExpressionResult(
                value=result,
                expression_type=expr_type,
                column_dependencies=self.column_dependencies.copy(),
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Expression evaluation failed: {e}"
            self.log_error(error_msg)
            
            return ExpressionResult(
                value=False,
                expression_type=ExpressionType.BOOLEAN,
                column_dependencies=[],
                execution_time=execution_time,
                error_message=error_msg
            )

    def _normalize_expression(self, expression: str) -> str:
        """
        Normalize expression string for parsing.
        
        Args:
            expression: Raw expression string
            
        Returns:
            Normalized expression string
        """
        # Convert logical operators to Python syntax
        expression = re.sub(r'AND', ' and ', expression, flags=re.IGNORECASE)
        expression = re.sub(r'OR', ' or ', expression, flags=re.IGNORECASE)
        expression = re.sub(r'NOT', ' not ', expression, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        expression = ' '.join(expression.split())
        
        return expression
    
    def _validate_ast(self, tree: ast.AST) -> None:
        """
        Validate AST for security (no unsafe operations).
        
        Args:
            tree: AST tree to validate
            
        Raises:
            SecurityError: If unsafe operations are found
        """
        for node in ast.walk(tree):
            # Check for unsafe node types
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, 
                               ast.ClassDef, ast.Global, ast.Nonlocal)):
                raise SecurityError(f"Unsafe operation: {type(node).__name__}")
            
            # Check for unsafe function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if not hasattr(self.statistical_functions, func_name):
                        raise SecurityError(f"Unknown function: {func_name}")
                elif isinstance(node.func, ast.Attribute):
                    raise SecurityError("Attribute access not allowed")
    
    def _evaluate_node(self, node: ast.AST) -> Union[float, bool, np.ndarray]:
        """
        Evaluate a single AST node.
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Evaluation result
        """
        if isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        
        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name in self.variables:
                if var_name not in self.column_dependencies:
                    self.column_dependencies.append(var_name)
                return self.variables[var_name]
            else:
                raise EvaluationError(f"Unknown variable: {var_name}")
        
        elif isinstance(node, ast.BinOp):
            left = self._evaluate_node(node.left)
            right = self._evaluate_node(node.right)
            op = self.BINARY_OPERATORS.get(type(node.op))
            
            if op is None:
                raise EvaluationError(f"Unsupported binary operator: {type(node.op)}")
            
            return op(left, right)
        
        elif isinstance(node, ast.UnaryOp):
            operand = self._evaluate_node(node.operand)
            op = self.UNARY_OPERATORS.get(type(node.op))
            
            if op is None:
                raise EvaluationError(f"Unsupported unary operator: {type(node.op)}")
            
            return op(operand)
        
        elif isinstance(node, ast.Compare):
            left = self._evaluate_node(node.left)
            
            for op, comparator in zip(node.ops, node.comparators):
                right = self._evaluate_node(comparator)
                comp_op = self.COMPARISON_OPERATORS.get(type(op))
                
                if comp_op is None:
                    raise EvaluationError(f"Unsupported comparison operator: {type(op)}")
                
                result = comp_op(left, right)
                
                # For chained comparisons, left becomes the result for next comparison
                left = right
            
            return result
        
        elif isinstance(node, ast.BoolOp):
            values = [self._evaluate_node(value) for value in node.values]
            op = self.BOOLEAN_OPERATORS.get(type(node.op))
            
            if op is None:
                raise EvaluationError(f"Unsupported boolean operator: {type(node.op)}")
            
            # Apply operator sequentially
            result = values[0]
            for value in values[1:]:
                result = op(result, value)
            
            return result
        
        elif isinstance(node, ast.Call):
            return self._evaluate_function_call(node)
        
        else:
            raise EvaluationError(f"Unsupported AST node: {type(node)}")

    def _evaluate_function_call(self, node: ast.Call) -> Union[float, np.ndarray]:
        """
        Evaluate function call node.
        
        Args:
            node: Function call AST node
            
        Returns:
            Function result
        """
        if not isinstance(node.func, ast.Name):
            raise EvaluationError("Only simple function calls are supported")
        
        func_name = node.func.id
        
        if not hasattr(self.statistical_functions, func_name):
            raise EvaluationError(f"Unknown function: {func_name}")
        
        # Evaluate arguments
        args = []
        for arg in node.args:
            args.append(self._evaluate_node(arg))
        
        # Evaluate keyword arguments
        kwargs = {}
        for keyword in node.keywords:
            kwargs[keyword.arg] = self._evaluate_node(keyword.value)
        
        # Call function
        func = getattr(self.statistical_functions, func_name)
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise EvaluationError(f"Function {func_name} failed: {e}")
    
    def validate_expression(self, expression: str, columns: List[str]) -> Dict[str, Any]:
        """
        Validate expression syntax and column dependencies.
        
        Args:
            expression: Expression to validate
            columns: Available column names
            
        Returns:
            Validation result dictionary
        """
        try:
            # Parse expression
            tree = self.parse_expression(expression)
            
            # Check column dependencies
            referenced_columns = []
            unknown_columns = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    var_name = node.id
                    if var_name not in ['and', 'or', 'not']:  # Skip logical operators
                        referenced_columns.append(var_name)
                        if var_name not in columns:
                            unknown_columns.append(var_name)
            
            referenced_columns = list(set(referenced_columns))  # Remove duplicates
            
            return {
                'valid': len(unknown_columns) == 0,
                'referenced_columns': referenced_columns,
                'unknown_columns': unknown_columns,
                'error_message': f"Unknown columns: {unknown_columns}" if unknown_columns else None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'referenced_columns': [],
                'unknown_columns': [],
                'error_message': str(e)
            }
    
    def get_available_functions(self) -> List[Dict[str, str]]:
        """
        Get list of available statistical functions.
        
        Returns:
            List of function information dictionaries
        """
        functions = []
        
        for name in dir(self.statistical_functions):
            if not name.startswith('_'):
                func = getattr(self.statistical_functions, name)
                if callable(func):
                    functions.append({
                        'name': name,
                        'description': func.__doc__ or f"{name} function",
                        'signature': self._get_function_signature(func)
                    })
        
        return functions
    
    def _get_function_signature(self, func: Callable) -> str:
        """
        Get function signature string.
        
        Args:
            func: Function to inspect
            
        Returns:
            Function signature string
        """
        import inspect
        try:
            sig = inspect.signature(func)
            return f"{func.__name__}{sig}"
        except Exception:
            return f"{func.__name__}(...)"


# Convenience function for quick expression evaluation
def evaluate_expression(expression: str, data: pd.DataFrame) -> ExpressionResult:
    """
    Evaluate expression against DataFrame (convenience function).
    
    Args:
        expression: Mathematical expression string
        data: DataFrame with column data
        
    Returns:
        ExpressionResult with evaluation results
    """
    parser = ExpressionParser()
    return parser.evaluate_expression(expression, data)


# Convenience function for expression validation
def validate_expression(expression: str, columns: List[str]) -> Dict[str, Any]:
    """
    Validate expression syntax and dependencies (convenience function).
    
    Args:
        expression: Expression to validate
        columns: Available column names
        
    Returns:
        Validation result dictionary
    """
    parser = ExpressionParser()
    return parser.validate_expression(expression, columns)
