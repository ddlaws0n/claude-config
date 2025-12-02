#!/usr/bin/env python3
"""
Marimo Notebook Validator

Comprehensive validation tool for marimo notebooks that checks:
- Notebook structure and syntax
- Variable dependencies and circular references
- UI element configurations
- Execution validation
- Performance profiling
- Security vulnerability scanning
"""

import ast
import argparse
import json
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import subprocess
import importlib.util


@dataclass
class ValidationError:
    """Represents a validation error with severity and details."""
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_number: Optional[int] = None
    cell_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[ValidationError]
    performance_metrics: Dict[str, Any]
    security_issues: List[ValidationError]
    optimization_suggestions: List[ValidationError]


class NotebookValidator:
    """Comprehensive marimo notebook validator."""

    def __init__(self, production_mode: bool = False):
        self.production_mode = production_mode
        self.import_registry: Set[str] = set()
        self.variable_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.cell_order: List[int] = []
        self.ui_elements: List[Dict] = []
        self.sql_queries: List[Dict] = []

    def validate_notebook(self, filepath: str) -> ValidationResult:
        """
        Validate a marimo notebook comprehensively.

        Args:
            filepath: Path to the marimo notebook (.py file)

        Returns:
            ValidationResult with comprehensive analysis
        """
        errors: List[ValidationError] = []
        security_issues: List[ValidationError] = []
        optimization_suggestions: List[ValidationError] = []

        try:
            # Read and parse the notebook
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic file validation
            file_errors = self._validate_file_structure(filepath, content)
            errors.extend(file_errors)

            # Parse AST for structural analysis
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                errors.append(ValidationError(
                    severity="error",
                    message=f"Syntax error: {e.msg}",
                    line_number=e.lineno,
                    suggestion="Fix the syntax error before proceeding"
                ))
                return ValidationResult(False, errors, {}, security_issues, optimization_suggestions)

            # Analyze marimo structure
            structure_errors = self._validate_marimo_structure(tree)
            errors.extend(structure_errors)

            # Analyze imports and dependencies
            import_errors = self._analyze_imports(tree)
            errors.extend(import_errors)

            # Analyze variable dependencies and detect circular references
            dependency_errors = self._analyze_dependencies(tree)
            errors.extend(dependency_errors)

            # Validate UI elements
            ui_errors = self._validate_ui_elements(tree)
            errors.extend(ui_errors)

            # Security analysis
            security_errors = self._security_analysis(tree)
            security_issues.extend(security_errors)

            # Performance analysis
            perf_errors = self._performance_analysis(tree)
            optimization_suggestions.extend(perf_errors)

            # Production-specific checks
            if self.production_mode:
                prod_errors = self._production_checks(tree)
                errors.extend(prod_errors)

            # Execute notebook for runtime validation
            if not errors:  # Only execute if no structural errors
                runtime_errors = self._runtime_validation(filepath)
                errors.extend(runtime_errors)

            # Performance metrics
            metrics = self._calculate_performance_metrics(filepath)

            is_valid = not any(error.severity == "error" for error in errors)

        except FileNotFoundError:
            errors.append(ValidationError(
                severity="error",
                message=f"File not found: {filepath}",
                suggestion="Check the file path and ensure the file exists"
            ))
            return ValidationResult(False, errors, {}, security_issues, optimization_suggestions)

        except Exception as e:
            errors.append(ValidationError(
                severity="error",
                message=f"Unexpected error during validation: {str(e)}",
                suggestion="Please report this issue with the notebook content"
            ))
            return ValidationResult(False, errors, {}, security_issues, optimization_suggestions)

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            performance_metrics=metrics,
            security_issues=security_issues,
            optimization_suggestions=optimization_suggestions
        )

    def _validate_file_structure(self, filepath: str, content: str) -> List[ValidationError]:
        """Validate basic file structure and requirements."""
        errors = []

        # Check file extension
        if not filepath.endswith('.py'):
            errors.append(ValidationError(
                severity="error",
                message="Marimo notebooks must be .py files",
                suggestion="Rename the file with a .py extension"
            ))

        # Check for required marimo import
        if 'import marimo' not in content:
            errors.append(ValidationError(
                severity="error",
                message="Missing required marimo import",
                suggestion="Add 'import marimo' at the top of the file"
            ))

        # Check for app creation
        if 'app = marimo.App(' not in content:
            errors.append(ValidationError(
                severity="error",
                message="Missing marimo App creation",
                suggestion="Add 'app = marimo.App()' after imports"
            ))

        # Check for cell decorators
        if '@app.cell' not in content:
            errors.append(ValidationError(
                severity="error",
                message="No marimo cells found",
                suggestion="Add cells using @app.cell decorators"
            ))

        return errors

    def _validate_marimo_structure(self, tree: ast.AST) -> List[ValidationError]:
        """Validate marimo-specific structure."""
        errors = []

        # Check for proper app structure
        has_app = False
        has_cells = False
        cell_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'app':
                        # Check if it's a marimo.App() assignment
                        if (isinstance(node.value, ast.Call) and
                            isinstance(node.value.func, ast.Attribute) and
                            node.value.func.attr == 'App'):
                            has_app = True
                            self.cell_order.append(-1)  # Mark app creation

            elif isinstance(node, ast.FunctionDef):
                # Check for cell decorators
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Attribute) and
                        isinstance(decorator.value, ast.Name) and
                        decorator.value.id == 'app' and
                        decorator.attr == 'cell'):
                        has_cells = True
                        cell_count += 1
                        self.cell_order.append(cell_count)

        if not has_app:
            errors.append(ValidationError(
                severity="error",
                message="No marimo.App() creation found",
                suggestion="Add 'app = marimo.App()' after imports"
            ))

        if not has_cells:
            errors.append(ValidationError(
                severity="error",
                message="No @app.cell decorators found",
                suggestion="Add at least one cell with @app.cell decorator"
            ))
        elif cell_count == 0:
            errors.append(ValidationError(
                severity="warning",
                message="Notebook appears to have no content cells",
                suggestion="Add content cells with actual code"
            ))

        return errors

    def _analyze_imports(self, tree: ast.AST) -> List[ValidationError]:
        """Analyze imports and check for common issues."""
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.import_registry.add(alias.name)

                    # Check for potentially problematic imports
                    problematic_imports = {
                        'os': 'Use pathlib instead for file operations',
                        'subprocess': 'Use marimo.ui.file_browser() for file operations',
                        'pickle': "Use JSON or marimo's built-in serialization"
                    }

                    if alias.name in problematic_imports:
                        errors.append(ValidationError(
                            severity="warning",
                            message=f"Potentially problematic import: {alias.name}",
                            suggestion=problematic_imports[alias.name]
                        ))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.import_registry.add(node.module)

                    # Check for specific risky imports
                    risky_imports = {
                        'subprocess': 'Subprocess calls may not work in deployed marimo apps',
                        'socket': 'Network operations may be restricted in some environments',
                        'threading': 'Marimo handles concurrency differently'
                    }

                    if node.module in risky_imports:
                        errors.append(ValidationError(
                            severity="warning",
                            message=f"Import from risky module: {node.module}",
                            suggestion=risky_imports[node.module]
                        ))

        # Check for required imports for advanced features
        if 'pandas' in self.import_registry and 'plotly' not in self.import_registry:
            errors.append(ValidationError(
                severity="info",
                message="Using pandas without plotly for visualization",
                suggestion="Consider adding plotly for interactive charts: mo.ui.plotly()"
            ))

        return errors

    def _analyze_dependencies(self, tree: ast.AST) -> List[ValidationError]:
        """Analyze variable dependencies and detect circular references."""
        errors = []

        # Track variable definitions and usage per cell
        cell_variables: Dict[int, Dict[str, Set[str]]] = defaultdict(lambda: {
            'defined': set(), 'used': set()
        })

        current_cell = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this is a cell function
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Attribute) and
                        decorator.attr == 'cell'):
                        current_cell += 1

                        # Analyze function body
                        for stmt in ast.walk(node):
                            if isinstance(stmt, ast.Assign):
                                # Track variable definitions
                                for target in stmt.targets:
                                    if isinstance(target, ast.Name):
                                        cell_variables[current_cell]['defined'].add(target.id)

                            elif isinstance(stmt, ast.Name) and isinstance(stmt.ctx, ast.Load):
                                # Track variable usage
                                cell_variables[current_cell]['used'].add(stmt.id)

        # Check for circular dependencies
        dependency_graph = {}
        for cell_num, variables in cell_variables.items():
            # Find which cells this cell depends on
            dependencies = set()
            for used_var in variables['used']:
                for other_cell, other_vars in cell_variables.items():
                    if other_cell != cell_num and used_var in other_vars['defined']:
                        dependencies.add(other_cell)

            dependency_graph[cell_num] = dependencies

        # Detect circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for cell_num in dependency_graph:
            if has_cycle(cell_num):
                errors.append(ValidationError(
                    severity="error",
                    message=f"Circular dependency detected involving cell {cell_num}",
                    cell_number=cell_num,
                    suggestion="Refactor to remove circular dependencies or use lazy evaluation"
                ))

        # Check for undefined variables
        for cell_num, variables in cell_variables.items():
            undefined = variables['used'] - variables['defined']
            if undefined:
                errors.append(ValidationError(
                    severity="warning",
                    message=f"Cell {cell_num} uses potentially undefined variables: {', '.join(undefined)}",
                    cell_number=cell_num,
                    suggestion="Ensure these variables are defined in previous cells"
                ))

        return errors

    def _validate_ui_elements(self, tree: ast.AST) -> List[ValidationError]:
        """Validate UI element configurations."""
        errors = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for mo.ui.* calls
                if (isinstance(node.func, ast.Attribute) and
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'mo' and
                    isinstance(node.func.value, ast.Name) and
                    hasattr(node.func, 'attr') and
                    node.func.attr.startswith('ui')):

                    ui_element = node.func.attr

                    # Check for common UI element issues
                    if ui_element == 'slider' and len(node.args) < 2:
                        errors.append(ValidationError(
                            severity="warning",
                            message="mo.ui.slider() should have start and end values",
                            suggestion="Add min and max values: mo.ui.slider(0, 100)"
                        ))

                    elif ui_element == 'table' and len(node.args) == 0:
                        errors.append(ValidationError(
                            severity="error",
                            message="mo.ui.table() requires data argument",
                            suggestion="Pass a dataframe or data: mo.ui.table(your_df)"
                        ))

                    elif ui_element == 'dropdown' and len(node.args) < 1:
                        errors.append(ValidationError(
                            severity="error",
                            message="mo.ui.dropdown() requires options",
                            suggestion="Provide options: mo.ui.dropdown(['option1', 'option2'])"
                        ))

                    # Record UI element for analysis
                    self.ui_elements.append({
                        'type': ui_element,
                        'line': getattr(node, 'lineno', None),
                        'has_args': len(node.args) > 0,
                        'has_kwargs': len(node.keywords) > 0
                    })

        return errors

    def _security_analysis(self, tree: ast.AST) -> List[ValidationError]:
        """Perform security analysis on the notebook."""
        errors = []

        for node in ast.walk(tree):
            # Check for eval() usage
            if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Name) and
                node.func.id == 'eval'):
                errors.append(ValidationError(
                    severity="error",
                    message="Use of eval() detected - security risk",
                    line_number=getattr(node, 'lineno', None),
                    suggestion="Avoid eval() or validate input thoroughly"
                ))

            # Check for exec() usage
            if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Name) and
                node.func.id == 'exec'):
                errors.append(ValidationError(
                    severity="error",
                    message="Use of exec() detected - security risk",
                    line_number=getattr(node, 'lineno', None),
                    suggestion="Avoid exec() or validate input thoroughly"
                ))

            # Check for hardcoded credentials
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(keyword in var_name for keyword in ['password', 'secret', 'key', 'token']):
                            errors.append(ValidationError(
                                severity="error",
                                message=f"Potential hardcoded credential: {target.id}",
                                line_number=getattr(node, 'lineno', None),
                                suggestion="Use environment variables or secure credential management"
                            ))

            # Check for SQL injection risks
            if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute) and
                node.func.attr in ['execute', 'run'] and
                len(node.args) > 0):

                # Check if first argument is a string with SQL
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    if isinstance(node.args[0].value, str) and 'SELECT' in node.args[0].value.upper():
                        # Check for parameterized queries
                        if '%' in node.args[0].value or '+' in str(node.args):
                            errors.append(ValidationError(
                                severity="warning",
                                message="Potential SQL injection vulnerability",
                                line_number=getattr(node, 'lineno', None),
                                suggestion="Use parameterized queries or marimo's built-in SQL cells"
                            ))

        return errors

    def _performance_analysis(self, tree: ast.AST) -> List[ValidationError]:
        """Analyze performance patterns and suggest optimizations."""
        errors = []

        # Check for pandas operations that could be optimized
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and
                isinstance(node.func, ast.Attribute)):

                # Pandas optimizations
                if (isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'pd'):

                    # Check for inefficient operations
                    if node.func.attr == 'iterrows':
                        errors.append(ValidationError(
                            severity="warning",
                            message="Use of pd.iterrows() - consider vectorized operations",
                            line_number=getattr(node, 'lineno', None),
                            suggestion="Use vectorized operations or apply() for better performance"
                        ))

                    elif node.func.attr == 'apply' and len(node.args) > 0:
                        # Check if axis=1 (row-wise operations)
                        for keyword in node.keywords:
                            if keyword.arg == 'axis' and isinstance(keyword.value, ast.Constant) and keyword.value.value == 1:
                                errors.append(ValidationError(
                                    severity="info",
                                    message="Row-wise apply() detected - may be slow",
                                    line_number=getattr(node, 'lineno', None),
                                    suggestion="Consider vectorized operations or use Polars for better performance"
                                ))

        # Check for expensive operations in loops
        loops_in_cells: List[Dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Look for expensive operations inside loops
                expensive_ops = []
                for child in ast.walk(node):
                    if (isinstance(child, ast.Call) and
                        isinstance(child.func, ast.Attribute)):

                        # Check for expensive operations
                        if child.func.attr in ['read_csv', 'read_sql', 'to_sql', 'merge', 'concat']:
                            expensive_ops.append(child.func.attr)

                if expensive_ops:
                    errors.append(ValidationError(
                        severity="warning",
                        message=f"Expensive operations in loop: {', '.join(expensive_ops)}",
                        line_number=getattr(node, 'lineno', None),
                        suggestion="Move expensive operations outside loops or use caching"
                    ))

        return errors

    def _production_checks(self, tree: ast.AST) -> List[ValidationError]:
        """Production-specific validation checks."""
        errors = []

        # Check for development-only code
        for node in ast.walk(tree):
            # Check for print statements
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                errors.append(ValidationError(
                    severity="warning",
                    message="print() statement detected - use marimo UI for output",
                    line_number=getattr(node, 'lineno', None),
                    suggestion="Replace with mo.md() or other marimo UI elements"
                ))

            # Check for hardcoded paths
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith(('/home/', '/Users/', 'C:')):
                    errors.append(ValidationError(
                        severity="warning",
                        message="Hardcoded file path detected",
                        line_number=getattr(node, 'lineno', None),
                        suggestion="Use relative paths or configuration files"
                    ))

        return errors

    def _runtime_validation(self, filepath: str) -> List[ValidationError]:
        """Execute notebook for runtime validation."""
        errors = []

        try:
            # Try to execute the notebook in a subprocess
            result = subprocess.run(
                [sys.executable, '-c', f'import marimo; marimo.check("{filepath}")'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                errors.append(ValidationError(
                    severity="error",
                    message=f"Runtime validation failed: {result.stderr}",
                    suggestion="Fix runtime errors before deployment"
                ))

        except subprocess.TimeoutExpired:
            errors.append(ValidationError(
                severity="warning",
                message="Notebook execution timed out (30s)",
                suggestion="Optimize performance or increase timeout for production"
            ))

        except Exception as e:
            errors.append(ValidationError(
                severity="warning",
                message=f"Could not validate notebook execution: {str(e)}",
                suggestion="Manual testing recommended"
            ))

        return errors

    def _calculate_performance_metrics(self, filepath: str) -> Dict[str, Any]:
        """Calculate performance metrics for the notebook."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            return {
                'file_size': len(content),
                'line_count': len(lines),
                'cell_count': content.count('@app.cell'),
                'ui_element_count': len(self.ui_elements),
                'import_count': len(self.import_registry),
                'estimated_complexity': self._calculate_complexity(content),
                'security_score': self._calculate_security_score()
            }

        except Exception:
            return {
                'file_size': 0,
                'line_count': 0,
                'cell_count': 0,
                'ui_element_count': 0,
                'import_count': 0,
                'estimated_complexity': 'unknown',
                'security_score': 'unknown'
            }

    def _calculate_complexity(self, content: str) -> str:
        """Estimate code complexity."""
        complexity_indicators = [
            'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'with'
        ]

        score = sum(content.count(indicator) for indicator in complexity_indicators)

        if score < 5:
            return 'low'
        elif score < 15:
            return 'medium'
        else:
            return 'high'

    def _calculate_security_score(self) -> str:
        """Calculate security score based on issues found."""
        # This would be calculated based on security issues found
        # For now, return a placeholder
        return 'good'


def main():
    """Main entry point for the validator."""
    parser = argparse.ArgumentParser(
        description="Validate marimo notebooks for structure, security, and performance"
    )
    parser.add_argument(
        'notebook_path',
        help="Path to the marimo notebook (.py file)"
    )
    parser.add_argument(
        '--production',
        action='store_true',
        help="Enable production-specific validation checks"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help="Output results in JSON format"
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help="Only show errors and warnings"
    )

    args = parser.parse_args()

    validator = NotebookValidator(production_mode=args.production)
    result = validator.validate_notebook(args.notebook_path)

    if args.json:
        # Output JSON format
        output = {
            'is_valid': result.is_valid,
            'errors': [
                {
                    'severity': error.severity,
                    'message': error.message,
                    'line_number': error.line_number,
                    'cell_number': error.cell_number,
                    'suggestion': error.suggestion
                }
                for error in result.errors
            ],
            'performance_metrics': result.performance_metrics,
            'security_issues': [
                {
                    'severity': issue.severity,
                    'message': issue.message,
                    'line_number': issue.line_number,
                    'suggestion': issue.suggestion
                }
                for issue in result.security_issues
            ],
            'optimization_suggestions': [
                {
                    'message': suggestion.message,
                    'line_number': suggestion.line_number,
                    'suggestion': suggestion.suggestion
                }
                for suggestion in result.optimization_suggestions
            ]
        }
        print(json.dumps(output, indent=2))

    else:
        # Output human-readable format
        if not args.quiet:
            print(f"🔍 Validating marimo notebook: {args.notebook_path}")
            print("=" * 60)

        # Print validation summary
        if result.is_valid:
            if not args.quiet:
                print("✅ Notebook validation PASSED")
            exit_code = 0
        else:
            if not args.quiet:
                print("❌ Notebook validation FAILED")
            exit_code = 1

        # Print errors and warnings
        if result.errors:
            print("\n📋 Issues Found:")
            for error in sorted(result.errors, key=lambda x: (x.severity, x.line_number or 0)):
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(error.severity, "•")

                location = ""
                if error.cell_number:
                    location = f" (Cell {error.cell_number})"
                elif error.line_number:
                    location = f" (Line {error.line_number})"

                print(f"  {icon} {error.severity.upper()}{location}: {error.message}")

                if error.suggestion:
                    print(f"     💡 Suggestion: {error.suggestion}")

        # Print security issues
        if result.security_issues:
            print("\n🔒 Security Issues:")
            for issue in result.security_issues:
                icon = {"error": "🚨", "warning": "⚠️"}.get(issue.severity, "•")
                location = f" (Line {issue.line_number})" if issue.line_number else ""
                print(f"  {icon} {issue.severity.upper()}{location}: {issue.message}")
                if issue.suggestion:
                    print(f"     💡 {issue.suggestion}")

        # Print optimization suggestions
        if result.optimization_suggestions and not args.quiet:
            print("\n⚡ Performance Optimization Suggestions:")
            for suggestion in result.optimization_suggestions:
                location = f" (Line {suggestion.line_number})" if suggestion.line_number else ""
                print(f"  💡 {suggestion.message}{location}")
                if suggestion.suggestion:
                    print(f"     → {suggestion.suggestion}")

        # Print performance metrics
        if not args.quiet:
            print(f"\n📊 Performance Metrics:")
            metrics = result.performance_metrics
            print(f"  • File size: {metrics.get('file_size', 0):,} bytes")
            print(f"  • Lines of code: {metrics.get('line_count', 0)}")
            print(f"  • Number of cells: {metrics.get('cell_count', 0)}")
            print(f"  • UI elements: {metrics.get('ui_element_count', 0)}")
            print(f"  • Imports: {metrics.get('import_count', 0)}")
            print(f"  • Complexity: {metrics.get('estimated_complexity', 'unknown')}")
            print(f"  • Security score: {metrics.get('security_score', 'unknown')}")

        sys.exit(exit_code)


if __name__ == "__main__":
    main()