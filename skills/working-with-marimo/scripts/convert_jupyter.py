#!/usr/bin/env python3
"""
Enhanced Jupyter to Marimo Converter

Converts Jupyter notebooks to marimo with advanced features:
- Automatic dependency analysis
- Code restructuring for marimo patterns
- Widget conversion
- Validation and optimization
- Conflict resolution
"""

import argparse
import json
import sys
import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
import subprocess


@dataclass
class ConversionIssue:
    """Represents a conversion issue or warning."""
    severity: str  # 'error', 'warning', 'info'
    message: str
    cell_index: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ConversionResult:
    """Container for conversion results."""
    success: bool
    marimo_code: str
    issues: List[ConversionIssue]
    statistics: Dict[str, Any]


class JupyterToMarimoConverter:
    """Enhanced Jupyter to marimo converter with validation."""

    def __init__(self, optimize: bool = False, validate: bool = True):
        self.optimize = optimize
        self.validate = validate
        self.variable_registry: Dict[str, int] = {}
        self.dependency_graph: Dict[int, Set[int]] = {}
        self.imports: Set[str] = set()
        self.widgets: List[Dict] = []

    def convert_notebook(self, input_path: str, output_path: Optional[str] = None) -> ConversionResult:
        """
        Convert Jupyter notebook to marimo.

        Args:
            input_path: Path to Jupyter notebook (.ipynb)
            output_path: Optional output path for marimo notebook

        Returns:
            ConversionResult with code and issues
        """
        issues = []

        try:
            # Read Jupyter notebook
            with open(input_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)

            # Validate notebook structure
            if 'cells' not in notebook:
                issues.append(ConversionIssue(
                    severity="error",
                    message="Invalid Jupyter notebook: no cells found",
                    suggestion="Ensure the file is a valid .ipynb file"
                ))
                return ConversionResult(False, "", issues, {})

            # Analyze cells and dependencies
            cell_analysis = self._analyze_cells(notebook['cells'], issues)

            # Restructure for marimo
            marimo_cells = self._restructure_cells(cell_analysis, issues)

            # Generate marimo code
            marimo_code = self._generate_marimo_code(marimo_cells, issues)

            # Optimize if requested
            if self.optimize:
                marimo_code = self._optimize_code(marimo_code, issues)

            # Validate result
            if self.validate:
                validation_issues = self._validate_result(marimo_code)
                issues.extend(validation_issues)

            # Save to file if path provided
            if output_path:
                self._save_marimo_notebook(marimo_code, output_path, issues)

            # Generate statistics
            statistics = self._generate_statistics(notebook, marimo_code, cell_analysis)

            success = not any(issue.severity == "error" for issue in issues)

            return ConversionResult(success, marimo_code, issues, statistics)

        except FileNotFoundError:
            issues.append(ConversionIssue(
                severity="error",
                message=f"File not found: {input_path}",
                suggestion="Check the file path and ensure the file exists"
            ))
            return ConversionResult(False, "", issues, {})

        except json.JSONDecodeError:
            issues.append(ConversionIssue(
                severity="error",
                message=f"Invalid JSON in notebook file: {input_path}",
                suggestion="Ensure the file is a valid JSON file"
            ))
            return ConversionResult(False, "", issues, {})

        except Exception as e:
            issues.append(ConversionIssue(
                severity="error",
                message=f"Unexpected error during conversion: {str(e)}",
                suggestion="Please report this issue with the notebook content"
            ))
            return ConversionResult(False, "", issues, {})

    def _analyze_cells(self, cells: List[Dict], issues: List[ConversionIssue]) -> List[Dict]:
        """Analyze Jupyter cells and extract information."""
        analysis = []

        for i, cell in enumerate(cells):
            if cell.get('cell_type') != 'code':
                continue

            source = ''.join(cell.get('source', []))
            if not source.strip():
                continue

            cell_info = {
                'index': i,
                'source': source,
                'imports': self._extract_imports(source),
                'variables_defined': self._extract_variables_defined(source),
                'variables_used': self._extract_variables_used(source),
                'has_widgets': self._detect_widgets(source),
                'has_magic': self._detect_magic_commands(source),
                'outputs': cell.get('outputs', []),
                'execution_count': cell.get('execution_count')
            }

            analysis.append(cell_info)

            # Track imports
            self.imports.update(cell_info['imports'])

            # Check for problematic patterns
            self._check_cell_issues(cell_info, issues)

        return analysis

    def _restructure_cells(self, cell_analysis: List[Dict], issues: List[ConversionIssue]) -> List[Dict]:
        """Restructure cells for optimal marimo execution."""
        # Build dependency graph
        self._build_dependency_graph(cell_analysis)

        # Sort cells by dependencies
        sorted_cells = self._topological_sort(cell_analysis)

        # Merge related cells
        merged_cells = self._merge_related_cells(sorted_cells, issues)

        # Convert widgets
        for cell in merged_cells:
            if cell['has_widgets']:
                cell['source'] = self._convert_widgets(cell['source'], issues)

        return merged_cells

    def _extract_imports(self, source: str) -> Set[str]:
        """Extract import statements from source code."""
        imports = set()

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
        except SyntaxError:
            # Handle syntax errors gracefully
            pass

        return imports

    def _extract_variables_defined(self, source: str) -> Set[str]:
        """Extract variables that are defined in the source."""
        variables = set()

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.add(target.id)
                elif isinstance(node, ast.FunctionDef):
                    variables.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    variables.add(node.name)
        except SyntaxError:
            pass

        return variables

    def _extract_variables_used(self, source: str) -> Set[str]:
        """Extract variables that are used in the source."""
        variables = set()

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    variables.add(node.id)
        except SyntaxError:
            pass

        return variables

    def _detect_widgets(self, source: str) -> bool:
        """Detect if the cell contains Jupyter widgets."""
        widget_patterns = [
            r'ipywidgets\.',
            r'from ipywidgets import',
            r'\.observe\(',
            r'\.value\s*=',
            r'widgets\.',
            r'interact\(',
            r'interactive\('
        ]

        return any(re.search(pattern, source) for pattern in widget_patterns)

    def _detect_magic_commands(self, source: str) -> bool:
        """Detect Jupyter magic commands."""
        magic_patterns = [
            r'^%[^%]',  # Line magic
            r'^%%',     # Cell magic
            r'!\s*\w+', # Shell commands
        ]

        for line in source.split('\n'):
            line = line.strip()
            for pattern in magic_patterns:
                if re.match(pattern, line):
                    return True
        return False

    def _check_cell_issues(self, cell_info: Dict, issues: List[ConversionIssue]):
        """Check for potential issues in cell content."""
        source = cell_info['source']

        # Check for problematic patterns
        if 'get_ipython()' in source:
            issues.append(ConversionIssue(
                severity="warning",
                message=f"get_ipython() detected in cell {cell_info['index']}",
                suggestion="Replace with marimo equivalents or remove IPython-specific code"
            ))

        if cell_info['has_magic']:
            issues.append(ConversionIssue(
                severity="warning",
                message=f"Jupyter magic commands detected in cell {cell_info['index']}",
                suggestion="Convert magic commands to regular Python or remove them"
            ))

        if 'plt.show()' in source:
            issues.append(ConversionIssue(
                severity="info",
                message=f"plt.show() detected in cell {cell_info['index']}",
                suggestion="marimo automatically displays matplotlib plots"
            ))

    def _build_dependency_graph(self, cell_analysis: List[Dict]):
        """Build dependency graph between cells."""
        for i, cell in enumerate(cell_analysis):
            dependencies = set()
            for j, other_cell in enumerate(cell_analysis):
                if i != j:
                    # Check if current cell uses variables defined in other cell
                    used_vars = cell['variables_used']
                    defined_vars = other_cell['variables_defined']
                    if used_vars & defined_vars:
                        dependencies.add(j)
            self.dependency_graph[i] = dependencies

    def _topological_sort(self, cell_analysis: List[Dict]) -> List[Dict]:
        """Sort cells topologically based on dependencies."""
        # Simple topological sort
        visited = set()
        temp_visited = set()
        result = []

        def visit(cell_idx):
            if cell_idx in temp_visited:
                # Circular dependency - use original order
                return
            if cell_idx in visited:
                return

            temp_visited.add(cell_idx)
            for dep in self.dependency_graph.get(cell_idx, set()):
                if dep < len(cell_analysis):
                    visit(dep)
            temp_visited.remove(cell_idx)
            visited.add(cell_idx)
            result.append(cell_analysis[cell_idx])

        for i in range(len(cell_analysis)):
            if i not in visited:
                visit(i)

        return result

    def _merge_related_cells(self, cells: List[Dict], issues: List[ConversionIssue]) -> List[Dict]:
        """Merge related cells for better marimo structure."""
        if len(cells) <= 1:
            return cells

        merged = []
        current_merge = cells[0]

        for i in range(1, len(cells)):
            cell = cells[i]

            # Merge criteria:
            # 1. Very small cells (< 3 lines)
            # 2. Cells that only define imports
            # 3. Related visualization cells
            should_merge = (
                len(cell['source'].split('\n')) <= 2 or
                (cell['imports'] and not cell['variables_defined']) or
                (current_merge['variables_defined'] and cell['source'].strip().startswith(('%matplotlib inline', 'plt')))
            )

            if should_merge:
                # Merge cells
                current_merge['source'] += '\n\n' + cell['source']
                current_merge['imports'].update(cell['imports'])
                current_merge['variables_defined'].update(cell['variables_defined'])
                current_merge['variables_used'].update(cell['variables_used'])
                current_merge['has_widgets'] = current_merge['has_widgets'] or cell['has_widgets']
                current_merge['has_magic'] = current_merge['has_magic'] or cell['has_magic']
                current_merge['outputs'].extend(cell['outputs'])
            else:
                merged.append(current_merge)
                current_merge = cell

        merged.append(current_merge)
        return merged

    def _convert_widgets(self, source: str, issues: List[ConversionIssue]) -> str:
        """Convert Jupyter widgets to marimo widgets."""
        # This is a simplified conversion - a full implementation would be more complex
        conversions = {
            r'from ipywidgets import ([^\n]+)': r'import marimo as mo\n# Converted ipywidgets: \1',
            r'widgets\.Slider': r'mo.ui.slider',
            r'widgets\.Dropdown': r'mo.ui.dropdown',
            r'widgets\.Text': r'mo.ui.text',
            r'widgets\.Button': r'mo.ui.button',
            r'widgets\.Checkbox': r'mo.ui.checkbox',
            r'interact\(': r'mo.ui.dropdown(options=',
        }

        converted = source
        issues.append(ConversionIssue(
            severity="warning",
            message="Widget conversion performed - manual review recommended",
            suggestion="Review converted widgets and adjust parameters as needed"
        ))

        for pattern, replacement in conversions.items():
            converted = re.sub(pattern, replacement, converted)

        return converted

    def _generate_marimo_code(self, cells: List[Dict], issues: List[ConversionIssue]) -> str:
        """Generate marimo notebook code from cells."""
        # Header
        header = '''import marimo

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def __():
    import marimo as mo
'''

        # Add collected imports
        if self.imports:
            for imp in sorted(self.imports):
                if imp != 'marimo':
                    header += f'    import {imp}\n'
        header += '    return mo,\n'

        if self.imports:
            header += '    ' + ', '.join(sorted(self.imports - {'marimo'})) + ',\n'

        header += '\n'

        # Cell content
        cell_content = []
        for i, cell in enumerate(cells):
            # Add cell separator
            cell_content.append(f'@app.cell\ndef __({self._generate_cell_signature(i)}):\n')

            # Add cell content
            cell_source = cell['source'].strip()
            if cell_source:
                # Indent the content
                indented_content = '\n    '.join(cell_source.split('\n'))
                cell_content.append(f'    {indented_content}\n')

            # Add return statement for defined variables
            if cell['variables_defined']:
                vars_to_return = ', '.join(sorted(cell['variables_defined']))
                cell_content.append(f'    return {vars_to_return},\n')
            else:
                cell_content.append('    return\n')

        return header + '\n'.join(cell_content)

    def _generate_cell_signature(self, cell_index: int) -> str:
        """Generate function signature for cell based on dependencies."""
        # This is simplified - a full implementation would analyze actual variable dependencies
        if cell_index == 0:
            return 'mo'

        # For now, just include mo and common variables
        common_vars = ['mo', 'pd', 'np', 'plt', 'px']
        return ', '.join(common_vars[:min(cell_index + 1, len(common_vars))])

    def _optimize_code(self, code: str, issues: List[ConversionIssue]) -> str:
        """Optimize the generated marimo code."""
        optimized = code

        # Remove duplicate imports
        lines = code.split('\n')
        import_lines = set()
        optimized_lines = []

        for line in lines:
            if line.strip().startswith('import '):
                if line.strip() not in import_lines:
                    import_lines.add(line.strip())
                    optimized_lines.append(line)
            else:
                optimized_lines.append(line)

        optimized = '\n'.join(optimized_lines)

        # Add optimization comments
        issues.append(ConversionIssue(
            severity="info",
            message="Code optimization applied",
            suggestion="Review optimized code for correctness"
        ))

        return optimized

    def _validate_result(self, marimo_code: str) -> List[ConversionIssue]:
        """Validate the generated marimo code."""
        issues = []

        # Check for required marimo structure
        if 'import marimo' not in marimo_code:
            issues.append(ConversionIssue(
                severity="error",
                message="Missing marimo import in generated code"
            ))

        if 'app = marimo.App(' not in marimo_code:
            issues.append(ConversionIssue(
                severity="error",
                message="Missing marimo.App creation in generated code"
            ))

        if '@app.cell' not in marimo_code:
            issues.append(ConversionIssue(
                severity="error",
                message="No marimo cells found in generated code"
            ))

        # Try to parse the generated code
        try:
            ast.parse(marimo_code)
        except SyntaxError as e:
            issues.append(ConversionIssue(
                severity="error",
                message=f"Syntax error in generated code: {e.msg}",
                suggestion="Review the generated code for syntax issues"
            ))

        return issues

    def _save_marimo_notebook(self, code: str, output_path: str, issues: List[ConversionIssue]):
        """Save the marimo notebook to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)

        except Exception as e:
            issues.append(ConversionIssue(
                severity="error",
                message=f"Failed to save output file: {str(e)}",
                suggestion="Check file permissions and disk space"
            ))

    def _generate_statistics(self, notebook: Dict, marimo_code: str, cell_analysis: List[Dict]) -> Dict[str, Any]:
        """Generate conversion statistics."""
        original_cells = len([c for c in notebook.get('cells', []) if c.get('cell_type') == 'code'])
        marimo_cells = marimo_code.count('@app.cell')

        return {
            'original_cells': original_cells,
            'marimo_cells': marimo_cells,
            'imports_converted': len(self.imports),
            'widgets_detected': sum(1 for cell in cell_analysis if cell['has_widgets']),
            'magic_commands_detected': sum(1 for cell in cell_analysis if cell['has_magic']),
            'original_size': len(json.dumps(notebook)),
            'marimo_size': len(marimo_code),
            'compression_ratio': len(marimo_code) / len(json.dumps(notebook)) if notebook else 0
        }


def main():
    """Main entry point for the converter."""
    parser = argparse.ArgumentParser(
        description="Convert Jupyter notebooks to marimo format"
    )
    parser.add_argument(
        'input_notebook',
        help="Path to input Jupyter notebook (.ipynb)"
    )
    parser.add_argument(
        '-o', '--output',
        help="Output path for marimo notebook (default: input_path.py)"
    )
    parser.add_argument(
        '--optimize',
        action='store_true',
        help="Optimize the generated code"
    )
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help="Skip validation of generated code"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help="Output results in JSON format"
    )
    parser.add_argument(
        '--run-check',
        action='store_true',
        help="Run marimo check on the generated notebook"
    )

    args = parser.parse_args()

    # Set output path if not provided
    if not args.output:
        input_path = Path(args.input_notebook)
        args.output = input_path.with_suffix('.py')

    # Create converter
    converter = JupyterToMarimoConverter(
        optimize=args.optimize,
        validate=not args.no_validate
    )

    # Convert notebook
    print(f"🔄 Converting {args.input_notebook} to {args.output}...")
    result = converter.convert_notebook(args.input_notebook, args.output)

    if args.json:
        # Output JSON format
        output = {
            'success': result.success,
            'marimo_code': result.marimo_code,
            'issues': [
                {
                    'severity': issue.severity,
                    'message': issue.message,
                    'cell_index': issue.cell_index,
                    'suggestion': issue.suggestion
                }
                for issue in result.issues
            ],
            'statistics': result.statistics
        }
        print(json.dumps(output, indent=2))

    else:
        # Output human-readable format
        print(f"{'✅' if result.success else '❌'} Conversion {'completed successfully' if result.success else 'failed'}")

        if result.issues:
            print(f"\n📋 Issues Found ({len(result.issues)}):")
            for issue in result.issues:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
                location = f" (Cell {issue.cell_index})" if issue.cell_index is not None else ""
                print(f"  {icon} {issue.severity.upper()}{location}: {issue.message}")
                if issue.suggestion:
                    print(f"     💡 {issue.suggestion}")

        print(f"\n📊 Conversion Statistics:")
        stats = result.statistics
        print(f"  • Original cells: {stats['original_cells']}")
        print(f"  • Marimo cells: {stats['marimo_cells']}")
        print(f"  • Imports converted: {stats['imports_converted']}")
        print(f"  • Widgets detected: {stats['widgets_detected']}")
        print(f"  • Magic commands: {stats['magic_commands_detected']}")
        print(f"  • Size reduction: {(1 - stats['compression_ratio']) * 100:.1f}%")

        if result.success:
            print(f"\n🚀 Generated marimo notebook: {args.output}")
            print(f"\nTo use the notebook:")
            print(f"  marimo edit {args.output}")
            print(f"  marimo run {args.output}")

            # Run marimo check if requested
            if args.run_check:
                print(f"\n🔍 Running marimo check...")
                try:
                    check_result = subprocess.run(
                        ['marimo', 'check', args.output],
                        capture_output=True,
                        text=True
                    )
                    if check_result.returncode == 0:
                        print("✅ Marimo check passed")
                    else:
                        print("⚠️ Marimo check found issues:")
                        print(check_result.stderr)
                except FileNotFoundError:
                    print("⚠️ Marimo not found - skip validation")
                except Exception as e:
                    print(f"⚠️ Error running marimo check: {e}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()