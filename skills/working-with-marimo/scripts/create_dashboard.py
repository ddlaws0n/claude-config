#!/usr/bin/env python3
"""
Marimo Dashboard Creator

Creates interactive dashboards from templates with advanced features:
- Multiple dashboard templates
- Configuration-based customization
- Data source integration
- Responsive design
- Performance optimization
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class DashboardTemplate:
    """Base class for dashboard templates."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate the dashboard code."""
        raise NotImplementedError


class InteractiveDashboardTemplate(DashboardTemplate):
    """Interactive data dashboard template."""

    def __init__(self):
        super().__init__(
            "dashboard",
            "Interactive data dashboard with filters, charts, and real-time updates"
        )

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate interactive dashboard code."""
        title = config.get('title', 'Interactive Dashboard')
        data_source = config.get('data_source', 'data.csv')
        chart_type = config.get('chart_type', 'line')
        filters = config.get('filters', ['date_range', 'segment', 'metric'])

        template = f'''import marimo
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from datetime import datetime, timedelta
    return mo, pd, px, datetime, timedelta

@app.cell
def __(mo):
    mo.md(f"# {title}")
    return

@app.cell
def __(mo, pd):
    """Data loading with error handling"""
    def load_data():
        try:
            # Try to load data from file
            data = pd.read_csv("{data_source}")

            # Convert date columns if they exist
            date_cols = data.select_dtypes(include=['object']).columns
            for col in date_cols:
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        data[col] = pd.to_datetime(data[col])
                    except:
                        pass

            return data
        except FileNotFoundError:
            # Create sample data if file doesn't exist
            mo.md(f"⚠️ **Data file '{data_source}' not found. Using sample data.**")
            return create_sample_data()
        except Exception as e:
            mo.md(f"❌ **Error loading data: {{str(e)}}**")
            return pd.DataFrame()

    def create_sample_data():
        """Create sample data for demonstration"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        sample_data = []

        for date in dates:
            sample_data.append({{
                'date': date,
                'revenue': float(1000 + (date.dayofyear * 10) + (hash(str(date)) % 500)),
                'users': int(100 + (date.dayofyear * 2) + (hash(str(date)) % 100)),
                'conversion': float(0.1 + (date.dayofyear % 50) / 500),
                'segment': ['all', 'mobile', 'desktop'][date.dayofyear % 3]
            }})

        return pd.DataFrame(sample_data)

    # Load data
    data = load_data()

    # Show data info
    if not data.empty:
        mo.md(f"📊 **Dataset Info**: {{data.shape[0]}} rows, {{data.shape[1]}} columns")
    else:
        mo.md("❌ **No data available**")

    return data, load_data, create_sample_data

@app.cell
def __(data, mo):
    """Interactive controls and filters"""
    if data.empty:
        controls = mo.ui.dictionary({{
            'message': mo.md("No data available for filtering")
        }})
    else:
        # Date range filter
        date_cols = [col for col in data.columns if 'date' in col.lower()]
        if date_cols:
            date_col = date_cols[0]
            min_date = data[date_col].min().date()
            max_date = data[date_col].max().date()

            date_filter = mo.ui.date_range(
                start=min_date,
                stop=max_date,
                value=(min_date, max_date),
                label="Date Range"
            )
        else:
            date_filter = mo.md("No date column found")

        # Segment filter
        segment_cols = [col for col in data.columns if 'segment' in col.lower() or 'category' in col.lower()]
        if segment_cols:
            segment_col = segment_cols[0]
            segments = ['all'] + list(data[segment_col].unique())
            segment_filter = mo.ui.multiselect(
                options=segments,
                value=['all'],
                label="Segment"
            )
        else:
            segment_filter = mo.md("No segment column found")

        # Metric selector
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            metric_filter = mo.ui.dropdown(
                options=numeric_cols,
                value=numeric_cols[0] if numeric_cols else None,
                label="Metric"
            )
        else:
            metric_filter = mo.md("No numeric columns found")

        # Chart type selector
        chart_type_filter = mo.ui.dropdown(
            options=['line', 'bar', 'scatter', 'area'],
            value='{chart_type}',
            label="Chart Type"
        )

        controls = mo.ui.dictionary({{
            'date_range': date_filter,
            'segment': segment_filter,
            'metric': metric_filter,
            'chart_type': chart_type_filter
        }})

    controls
    return controls, date_filter, segment_filter, metric_filter, chart_type_filter

@app.cell
def __(data, controls, mo, px):
    """Data filtering and visualization"""
    def filter_data(df, controls_value):
        """Filter data based on controls"""
        if df.empty:
            return df

        filtered_df = df.copy()

        # Apply date filter
        if 'date_range' in controls_value and hasattr(controls_value['date_range'], 'value'):
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols:
                date_col = date_cols[0]
                start_date, end_date = controls_value['date_range'].value
                filtered_df = filtered_df[
                    (filtered_df[date_col].dt.date >= start_date) &
                    (filtered_df[date_col].dt.date <= end_date)
                ]

        # Apply segment filter
        if 'segment' in controls_value and hasattr(controls_value['segment'], 'value'):
            segment_cols = [col for col in df.columns if 'segment' in col.lower() or 'category' in col.lower()]
            if segment_cols and 'all' not in controls_value['segment'].value:
                segment_col = segment_cols[0]
                filtered_df = filtered_df[
                    filtered_df[segment_col].isin(controls_value['segment'].value)
                ]

        return filtered_df

    def create_chart(df, controls_value):
        """Create chart based on selected options"""
        if df.empty:
            return mo.md("No data to display")

        filtered_df = filter_data(df, controls_value)

        if filtered_df.empty:
            return mo.md("No data matches the current filters")

        # Get chart configuration
        chart_type = controls_value.get('chart_type', 'line')
        if hasattr(chart_type, 'value'):
            chart_type = chart_type.value

        metric = controls_value.get('metric')
        if hasattr(metric, 'value'):
            metric = metric.value

        if not metric or metric not in filtered_df.columns:
            return mo.md("Invalid metric selection")

        # Find date column for x-axis
        date_cols = [col for col in filtered_df.columns if 'date' in col.lower()]
        x_col = date_cols[0] if date_cols else filtered_df.columns[0]

        # Create chart based on type
        if chart_type == 'line':
            fig = px.line(
                filtered_df,
                x=x_col,
                y=metric,
                title=f"{{metric.title()}} Over Time"
            )
        elif chart_type == 'bar':
            fig = px.bar(
                filtered_df,
                x=x_col,
                y=metric,
                title=f"{{metric.title()}} by {{x_col.title()}}"
            )
        elif chart_type == 'scatter':
            numeric_cols = filtered_df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                fig = px.scatter(
                    filtered_df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{{numeric_cols[0].title()}} vs {{numeric_cols[1].title()}}"
                )
            else:
                fig = px.scatter(
                    filtered_df,
                    x=x_col,
                    y=metric,
                    title=f"{{metric.title()}} by {{x_col.title()}}"
                )
        elif chart_type == 'area':
            fig = px.area(
                filtered_df,
                x=x_col,
                y=metric,
                title=f"{{metric.title()}} Over Time"
            )
        else:
            fig = px.line(
                filtered_df,
                x=x_col,
                y=metric,
                title=f"{{metric.title()}} Over Time"
            )

        # Improve layout
        fig.update_layout(
            height=400,
            showlegend=True,
            template="plotly_white"
        )

        return mo.ui.plotly(fig)

    # Create chart (reactive to controls)
    chart = create_chart(data, controls.value)

    chart
    return chart, filter_data, create_chart

@app.cell
def __(data, mo):
    """Data summary table"""
    def create_summary_table(df):
        """Create summary statistics table"""
        if df.empty:
            return mo.md("No data available")

        # Basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            return mo.md("No numeric columns for statistics")

        summary_data = []
        for col in numeric_cols:
            summary_data.append({{
                'Metric': col,
                'Count': len(df[col].dropna()),
                'Mean': f"{{df[col].mean():.2f}}",
                'Median': f"{{df[col].median():.2f}}",
                'Std Dev': f"{{df[col].std():.2f}}",
                'Min': f"{{df[col].min():.2f}}",
                'Max': f"{{df[col].max():.2f}}"
            }})

        summary_df = pd.DataFrame(summary_data)
        return mo.ui.table(summary_df, selection=None)

    # Create summary table
    summary_table = create_summary_table(data)

    mo.md("## 📈 Data Summary")
    summary_table
    return summary_table, create_summary_table

@app.cell
def __(mo, data):
    """Data quality indicators"""
    def check_data_quality(df):
        """Check data quality and return status indicators"""
        if df.empty:
            return {
                'has_data': False,
                'missing_data': True,
                'duplicates': True,
                'data_types': True
            }

        quality_checks = {
            'has_data': len(df) > 0,
            'missing_data': df.isnull().any().any(),
            'duplicates': df.duplicated().any(),
            'data_types': True  # Assume good for now
        }

        return quality_checks

    quality = check_data_quality(data)

    # Create quality indicators
    quality_items = []
    if quality['has_data']:
        quality_items.append(("✅", "Data loaded successfully"))
    else:
        quality_items.append(("❌", "No data available"))

    if quality['missing_data']:
        quality_items.append(("⚠️", "Missing data detected"))
    else:
        quality_items.append(("✅", "No missing data"))

    if quality['duplicates']:
        quality_items.append(("⚠️", "Duplicate rows detected"))
    else:
        quality_items.append(("✅", "No duplicate rows"))

    quality_md = "\\n".join([f"{{icon}} {{item}}" for icon, item in quality_items])

    mo.md(f"## 🔍 Data Quality\\n\\n{{quality_md}}")
    return quality, check_data_quality, quality_items

@app.cell
def __(mo):
    """Footer and instructions"""
    mo.md("""
    ## 📝 Instructions

    1. **Upload Data**: Replace `{data_source}` with your data file
    2. **Configure Filters**: Use the controls above to filter data
    3. **Explore Charts**: Select different metrics and chart types
    4. **Export Results**: Right-click on charts to save images

    ### Customization Tips:
    - Modify the `data_source` variable in the data loading cell
    - Add custom filters in the controls section
    - Enhance visualizations with Plotly Express options
    - Add additional data processing steps as needed

    Created with ❤️ using Marimo Dashboard Template
    """)
    return

if __name__ == "__main__":
    app.run()
'''

        return template


class AnalyticsTemplate(DashboardTemplate):
    """Data analytics workflow template."""

    def __init__(self):
        super().__init__(
            "analytics",
            "Comprehensive data analysis workflow with statistical analysis and reporting"
        )

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate analytics workflow code."""
        title = config.get('title', 'Data Analysis Workflow')
        data_source = config.get('data_source', 'data.csv')

        template = f'''import marimo
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import plotly.graph_objects as go
    from scipy import stats
    import seaborn as sns
    import matplotlib.pyplot as plt
    return mo, pd, np, px, go, stats, sns, plt

@app.cell
def __(mo):
    mo.md(f"# {title}")
    return

@app.cell
def __(pd, mo):
    """Data loading and initial exploration"""
    def load_and_explore_data(filepath):
        """Load data and perform initial exploration"""
        try:
            df = pd.read_csv(filepath)

            # Basic info
            info = {{
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'missing_values': df.isnull().sum().to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum()
            }}

            return df, info
        except Exception as e:
            mo.md(f"❌ **Error loading data: {{str(e)}}**")
            return None, None

    # Load data
    data, data_info = load_and_explore_data("{data_source}")

    if data is not None:
        mo.md(f"""
        ## 📊 Dataset Overview

        - **Shape**: {{data_info['shape'][0]}} rows × {{data_info['shape'][1]}} columns
        - **Memory Usage**: {{data_info['memory_usage'] / 1024 / 1024:.1f}} MB
        - **Columns**: {{', '.join(data_info['columns'])}}
        """)
    else:
        mo.md("❌ **Could not load data**")

    return data, data_info, load_and_explore_data

@app.cell
def __(data, mo, pd, np):
    """Data cleaning and preprocessing"""
    def clean_data(df):
        """Perform data cleaning operations"""
        if df is None:
            return None

        cleaned_df = df.copy()
        cleaning_report = []

        # Handle missing values
        missing_before = cleaned_df.isnull().sum().sum()

        # Drop columns with >50% missing values
        cols_to_drop = cleaned_df.columns[cleaned_df.isnull().mean() > 0.5]
        if len(cols_to_drop) > 0:
            cleaned_df = cleaned_df.drop(columns=cols_to_drop)
            cleaning_report.append(f"Dropped {{len(cols_to_drop)}} columns with >50% missing data")

        # Fill remaining missing values
        for col in cleaned_df.columns:
            if cleaned_df[col].isnull().any():
                if cleaned_df[col].dtype in ['object', 'category']:
                    cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].mode().iloc[0])
                else:
                    cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())

        missing_after = cleaned_df.isnull().sum().sum()

        if missing_before > missing_after:
            cleaning_report.append(f"Filled {{missing_before - missing_after}} missing values")

        # Remove duplicate rows
        duplicates_before = cleaned_df.duplicated().sum()
        cleaned_df = cleaned_df.drop_duplicates()
        duplicates_after = cleaned_df.duplicated().sum()

        if duplicates_before > duplicates_after:
            cleaning_report.append(f"Removed {{duplicates_before}} duplicate rows")

        return cleaned_df, cleaning_report

    # Clean data
    cleaned_data, cleaning_steps = clean_data(data)

    if cleaned_data is not None:
        mo.md("## 🧹 Data Cleaning")
        if cleaning_steps:
            for step in cleaning_steps:
                mo.md(f"✅ {{step}}")
        else:
            mo.md("✅ No cleaning needed")

    return cleaned_data, cleaning_steps, clean_data

@app.cell
def __(cleaned_data, mo, pd):
    """Statistical analysis"""
    def perform_statistical_analysis(df):
        """Perform comprehensive statistical analysis"""
        if df is None:
            return None

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        analysis_results = {{
            'descriptive_stats': df[numeric_cols].describe(),
            'correlation_matrix': df[numeric_cols].corr() if len(numeric_cols) > 1 else None,
            'numeric_cols': numeric_cols.tolist(),
            'categorical_cols': df.select_dtypes(include=['object', 'category']).columns.tolist()
        }}

        return analysis_results

    # Perform analysis
    stats_results = perform_statistical_analysis(cleaned_data)

    if stats_results:
        mo.md("## 📈 Statistical Analysis")

        # Descriptive statistics
        if not stats_results['descriptive_stats'].empty:
            mo.md("### Descriptive Statistics")
            stats_table = mo.ui.table(
                stats_results['descriptive_stats'].round(2),
                selection=None
            )
            stats_table

        # Correlation analysis
        if stats_results['correlation_matrix'] is not None:
            mo.md("### Correlation Matrix")
            corr_table = mo.ui.table(
                stats_results['correlation_matrix'].round(3),
                selection=None
            )
            corr_table

    return stats_results, perform_statistical_analysis

@app.cell
def __(cleaned_data, stats_results, mo, px):
    """Data visualization"""
    def create_visualizations(df, stats):
        """Create comprehensive visualizations"""
        if df is None or stats is None:
            return []

        visualizations = []
        numeric_cols = stats['numeric_cols']
        categorical_cols = stats['categorical_cols']

        # Histograms for numeric columns
        if numeric_cols:
            for col in numeric_cols[:4]:  # Limit to first 4 numeric columns
                fig = px.histogram(
                    df,
                    x=col,
                    title=f"Distribution of {{col}}",
                    nbins=30
                )
                fig.update_layout(height=300)
                visualizations.append(('histogram', col, fig))

        # Box plots for numeric columns
        if len(numeric_cols) >= 2:
            fig = px.box(
                df[numeric_cols[:6]],  # Limit to first 6 columns
                title="Box Plot of Numeric Variables"
            )
            fig.update_layout(height=400)
            visualizations.append(('boxplot', 'numeric', fig))

        # Categorical data visualization
        if categorical_cols:
            for col in categorical_cols[:2]:  # Limit to first 2 categorical columns
                value_counts = df[col].value_counts().head(10)
                fig = px.bar(
                    x=value_counts.index,
                    y=value_counts.values,
                    title=f"Top 10 {{col}} Values"
                )
                fig.update_layout(height=300)
                visualizations.append(('bar', col, fig))

        # Correlation heatmap
        if stats['correlation_matrix'] is not None:
            fig = px.imshow(
                stats['correlation_matrix'],
                title="Correlation Heatmap",
                color_continuous_scale="RdBu",
                aspect="auto"
            )
            fig.update_layout(height=400)
            visualizations.append(('heatmap', 'correlation', fig))

        return visualizations

    # Create visualizations
    visualizations = create_visualizations(cleaned_data, stats_results)

    if visualizations:
        mo.md("## 📊 Data Visualizations")

        for viz_type, col, fig in visualizations:
            mo.md(f"### {{viz_type.title()}} - {{col}}")
            mo.ui.plotly(fig)

    return visualizations, create_visualizations

@app.cell
def __(cleaned_data, stats_results, mo):
    """Advanced analysis and insights"""
    def generate_insights(df, stats):
        """Generate automated insights from the data"""
        if df is None or stats is None:
            return []

        insights = []
        numeric_cols = stats['numeric_cols']

        # Outlier detection
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]

            if len(outliers) > 0:
                outlier_pct = (len(outliers) / len(df)) * 100
                insights.append(f"📊 **{{col}}**: {{len(outliers)}} outliers detected ({{outlier_pct:.1f}}%)")

        # Correlation insights
        if stats['correlation_matrix'] is not None:
            high_corr_pairs = []
            corr_matrix = stats['correlation_matrix'].abs()

            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if corr_matrix.iloc[i, j] > 0.7:
                        high_corr_pairs.append(
                            (corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j])
                        )

            for col1, col2, corr_val in high_corr_pairs[:5]:  # Top 5 correlations
                insights.append(f"🔗 **Strong correlation**: {{col1}} and {{col2}} ({{corr_val:.3f}})")

        # Data quality insights
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_pct < 1:
            insights.append(f"✅ **Data quality**: Excellent ({{missing_pct:.2f}}% missing)")
        elif missing_pct < 5:
            insights.append(f"⚠️ **Data quality**: Good ({{missing_pct:.2f}}% missing)")
        else:
            insights.append(f"❌ **Data quality**: Needs improvement ({{missing_pct:.2f}}% missing)")

        return insights

    # Generate insights
    insights = generate_insights(cleaned_data, stats_results)

    if insights:
        mo.md("## 💡 Key Insights")
        for insight in insights:
            mo.md(insight)

    return insights, generate_insights

@app.cell
def __(mo):
    """Analysis summary and export options"""
    mo.md("""
    ## 📋 Analysis Summary

    This analytics workflow has performed:

    1. **Data Loading**: Loaded and validated your dataset
    2. **Data Cleaning**: Handled missing values and duplicates
    3. **Statistical Analysis**: Generated descriptive statistics and correlations
    4. **Visualization**: Created comprehensive charts and graphs
    5. **Insight Generation**: Identified key patterns and outliers

    ### Next Steps:
    - Review the generated insights
    - Export visualizations for reports
    - Apply additional domain-specific analysis
    - Consider feature engineering for machine learning

    ### Export Options:
    - Right-click on any chart to save as image
    - Use pandas to export cleaned data: `cleaned_data.to_csv('cleaned_data.csv')`
    - Save analysis results to reports or dashboards
    """)
    return

if __name__ == "__main__":
    app.run()
'''

        return template


class RealtimeTemplate(DashboardTemplate):
    """Real-time monitoring dashboard template."""

    def __init__(self):
        super().__init__(
            "realtime",
            "Real-time monitoring dashboard with live data streaming and alerts"
        )

    def generate(self, config: Dict[str, Any]) -> str:
        """Generate real-time monitoring dashboard code."""
        title = config.get('title', 'Real-time Monitor')

        template = f'''import marimo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import time
    import random
    return mo, pd, px, go, datetime, timedelta, time, random

@app.cell
def __(mo):
    mo.md(f"# {title}")
    return

@app.cell
def __(mo):
    """Real-time data generator and configuration"""
    # Configuration
    config = mo.ui.dictionary({{
        'update_interval': mo.ui.slider(
            1, 60,
            value=5,
            label="Update Interval (seconds)"
        ),
        'max_data_points': mo.ui.slider(
            50, 1000,
            value=200,
            label="Max Data Points"
        ),
        'alert_threshold': mo.ui.slider(
            0, 100,
            value=80,
            label="Alert Threshold (%)"
        ),
        'data_source': mo.ui.dropdown(
            ["simulated", "api", "file"],
            value="simulated",
            label="Data Source"
        )
    }})

    config
    return config

@app.cell
def __(mo, random, datetime):
    """State management for real-time data"""
    @mo.state
    def get_state():
        return {{
            'data': pd.DataFrame(),
            'last_update': datetime.now(),
            'alerts': [],
            'is_running': False
        }}

    state = get_state()
    return state, get_state

@app.cell
def __(state, mo, random, datetime):
    """Real-time data generator"""
    def generate_realtime_data():
        """Generate simulated real-time data"""
        now = datetime.now()

        # Generate new data point
        new_point = {{
            'timestamp': now,
            'cpu_usage': random.uniform(20, 90),
            'memory_usage': random.uniform(30, 85),
            'response_time': random.uniform(100, 500),
            'error_rate': random.uniform(0, 5),
            'active_users': random.randint(50, 200),
            'requests_per_second': random.uniform(10, 100)
        }}

        # Add to state
        state['data'] = pd.concat([state['data'], pd.DataFrame([new_point])], ignore_index=True)

        # Limit data points
        max_points = config.value['max_data_points']
        if len(state['data']) > max_points:
            state['data'] = state['data'].tail(max_points).copy()

        # Update timestamp
        state['last_update'] = now

        # Check for alerts
        check_alerts(new_point)

        return state['data']

    def check_alerts(data_point):
        """Check if alerts should be triggered"""
        threshold = config.value['alert_threshold']
        alerts = []

        if data_point['cpu_usage'] > threshold:
            alerts.append({{
                'timestamp': datetime.now(),
                'type': 'CPU High',
                'message': f"CPU usage at {{data_point['cpu_usage']:.1f}}%",
                'severity': 'warning' if data_point['cpu_usage'] < 90 else 'critical'
            }})

        if data_point['memory_usage'] > threshold:
            alerts.append({{
                'timestamp': datetime.now(),
                'type': 'Memory High',
                'message': f"Memory usage at {{data_point['memory_usage']:.1f}}%",
                'severity': 'warning' if data_point['memory_usage'] < 90 else 'critical'
            }})

        if data_point['error_rate'] > 2:
            alerts.append({{
                'timestamp': datetime.now(),
                'type': 'Error Rate High',
                'message': f"Error rate at {{data_point['error_rate']:.1f}}%",
                'severity': 'critical'
            }})

        # Add to state alerts (keep last 10)
        state['alerts'] = (alerts + state['alerts'])[:10]

    return generate_realtime_data, check_alerts

@app.cell
def __(state, mo, px):
    """Real-time status indicators"""
    def create_status_indicators():
        """Create status indicators dashboard"""
        if state['data'].empty:
            return mo.md("No data available yet...")

        latest = state['data'].iloc[-1]
        time_since_update = (datetime.now() - state['last_update']).total_seconds()

        # Status indicators
        status_items = []

        # Overall status
        if time_since_update < 10:
            status_items.append(("🟢", "System Online", f"Last update: {{time_since_update:.1f}}s ago"))
        else:
            status_items.append(("🔴", "System Offline", f"Last update: {{time_since_update:.1f}}s ago"))

        # CPU status
        cpu_color = "🟢" if latest['cpu_usage'] < 50 else "🟡" if latest['cpu_usage'] < 80 else "🔴"
        status_items.append((cpu_color, "CPU Usage", f"{{latest['cpu_usage']:.1f}}%"))

        # Memory status
        mem_color = "🟢" if latest['memory_usage'] < 50 else "🟡" if latest['memory_usage'] < 80 else "🔴"
        status_items.append((mem_color, "Memory Usage", f"{{latest['memory_usage']:.1f}}%"))

        # Response time
        resp_color = "🟢" if latest['response_time'] < 200 else "🟡" if latest['response_time'] < 400 else "🔴"
        status_items.append((resp_color, "Response Time", f"{{latest['response_time']:.0f}}ms"))

        # Active users
        status_items.append(("👥", "Active Users", f"{{int(latest['active_users'])}}"))

        # Create status display
        status_html = "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;'>"
        for icon, title, value in status_items:
            status_html += f"""
            <div style='padding: 1rem; border: 1px solid #ddd; border-radius: 8px; text-align: center;'>
                <div style='font-size: 2rem;'>{{icon}}</div>
                <div style='font-weight: bold;'>{{title}}</div>
                <div style='color: #666;'>{{value}}</div>
            </div>
            """
        status_html += "</div>"

        return mo.md(status_html)

    # Status indicators
    status_display = create_status_indicators()

    mo.md("## 📊 System Status")
    status_display
    return status_display, create_status_indicators

@app.cell
def __(state, mo, px, go):
    """Real-time charts"""
    def create_realtime_charts():
        """Create real-time updating charts"""
        if state['data'].empty:
            return mo.md("No data available for charts...")

        # Time series charts
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=state['data']['timestamp'],
            y=state['data']['cpu_usage'],
            mode='lines+markers',
            name='CPU Usage',
            line=dict(color='blue')
        ))
        fig1.add_trace(go.Scatter(
            x=state['data']['timestamp'],
            y=state['data']['memory_usage'],
            mode='lines+markers',
            name='Memory Usage',
            line=dict(color='red')
        ))
        fig1.update_layout(
            title='System Resources Over Time',
            xaxis_title='Time',
            yaxis_title='Usage (%)',
            height=400,
            yaxis=dict(range=[0, 100])
        )

        # Response time chart
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=state['data']['timestamp'],
            y=state['data']['response_time'],
            mode='lines+markers',
            name='Response Time',
            line=dict(color='green')
        ))
        fig2.update_layout(
            title='Response Time Over Time',
            xaxis_title='Time',
            yaxis_title='Response Time (ms)',
            height=300
        )

        # Metrics overview
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=state['data']['timestamp'],
            y=state['data']['active_users'],
            mode='lines+markers',
            name='Active Users',
            line=dict(color='purple')
        ))
        fig3.add_trace(go.Scatter(
            x=state['data']['timestamp'],
            y=state['data']['requests_per_second'],
            mode='lines+markers',
            name='Requests/sec',
            yaxis='y2',
            line=dict(color='orange')
        ))
        fig3.update_layout(
            title='User Activity Over Time',
            xaxis_title='Time',
            yaxis=dict(title='Active Users'),
            yaxis2=dict(title='Requests/sec', overlaying='y', side='right'),
            height=300
        )

        return (
            mo.ui.plotly(fig1),
            mo.ui.plotly(fig2),
            mo.ui.plotly(fig3)
        )

    # Create charts
    chart1, chart2, chart3 = create_realtime_charts()

    mo.md("## 📈 Real-time Metrics")
    chart1
    chart2
    chart3
    return chart1, chart2, chart3, create_realtime_charts

@app.cell
def __(state, mo):
    """Alerts panel"""
    def create_alerts_panel():
        """Create alerts display panel"""
        if not state['alerts']:
            return mo.md("✅ No active alerts")

        alert_html = "<div style='max-height: 300px; overflow-y: auto;'>"

        for alert in state['alerts']:
            severity_color = {{
                'warning': '#ffc107',
                'critical': '#dc3545'
            }}.get(alert['severity'], '#6c757d')

            alert_html += f"""
            <div style='padding: 0.75rem; margin: 0.5rem 0; border-left: 4px solid {{severity_color}}; background-color: #f8f9fa; border-radius: 4px;'>
                <div style='font-weight: bold; color: {{severity_color}};'>{{alert['type']}}</div>
                <div>{{alert['message']}}</div>
                <div style='font-size: 0.8em; color: #666;'>{{alert['timestamp'].strftime('%H:%M:%S')}}</div>
            </div>
            """

        alert_html += "</div>"

        return mo.md(alert_html)

    # Alerts panel
    alerts_panel = create_alerts_panel()

    mo.md("## 🚨 Alerts")
    alerts_panel
    return alerts_panel, create_alerts_panel

@app.cell
def __(mo, state):
    """Control panel for real-time updates"""
    def toggle_monitoring():
        """Toggle monitoring on/off"""
        state['is_running'] = not state['is_running']
        if state['is_running']:
            return "⏸️ Pause Monitoring"
        else:
            return "▶️ Start Monitoring"

    def update_data():
        """Update data function for real-time updates"""
        if state['is_running'] and not state['data'].empty:
            generate_realtime_data()

    # Control buttons
    start_stop_btn = mo.ui.button(
        label=toggle_monitoring(),
        on_click=lambda: toggle_monitoring()
    )

    clear_data_btn = mo.ui.button(
        label="🗑️ Clear Data",
        on_click=lambda: state.update({'data': pd.DataFrame(), 'alerts': []})
    )

    # Update data button
    update_btn = mo.ui.button(
        label="🔄 Update Now",
        on_click=update_data
    )

    # Display status and controls
    mo.md("## 🎛️ Control Panel")
    mo.md(f"**Status**: {'🟢 Running' if state['is_running'] else '🔴 Stopped'}")

    controls_row = mo.hstack([start_stop_btn, update_btn, clear_data_btn])
    controls_row
    return toggle_monitoring, update_data, start_stop_btn, clear_data_btn, update_btn, controls_row

@app.cell
def __(mo):
    """Documentation and instructions"""
    mo.md(f"""
    ## 📖 Real-time Monitor Documentation

    This real-time monitoring dashboard provides:

    ### Features:
    - **Live Data Streaming**: Simulated real-time data updates
    - **System Status**: CPU, Memory, Response Time monitoring
    - **Alert System**: Automatic threshold-based alerts
    - **Interactive Charts**: Real-time updating visualizations
    - **Control Panel**: Start/stop monitoring and data management

    ### Configuration:
    - **Update Interval**: How often to refresh data (1-60 seconds)
    - **Max Data Points**: Maximum historical data points to retain
    - **Alert Threshold**: CPU/Memory percentage for alert triggers
    - **Data Source**: Choose between simulated, API, or file data sources

    ### Usage:
    1. Click **▶️ Start Monitoring** to begin real-time updates
    2. Adjust configuration parameters as needed
    3. Monitor system status and alerts in real-time
    4. Use charts to analyze trends and patterns
    5. Export charts or data for further analysis

    ### Customization:
    - Modify data sources in the `generate_realtime_data()` function
    - Add custom alert conditions in `check_alerts()` function
    - Enhance visualizations with additional chart types
    - Integrate with actual monitoring APIs or databases

    ### Production Deployment:
    - Replace simulated data with real API endpoints
    - Add authentication and security measures
    - Implement persistent data storage
    - Set up proper error handling and recovery
    - Configure logging and monitoring of the monitor itself

    Created with ❤️ using Marimo Real-time Template
    """)
    return

if __name__ == "__main__":
    app.run()
'''

        return template


# Template registry
TEMPLATES = {
    'dashboard': InteractiveDashboardTemplate(),
    'analytics': AnalyticsTemplate(),
    'realtime': RealtimeTemplate(),
}


def main():
    """Main entry point for dashboard creator."""
    parser = argparse.ArgumentParser(
        description="Create marimo dashboards from templates"
    )
    parser.add_argument(
        'output_file',
        help="Output file path for the dashboard"
    )
    parser.add_argument(
        '--template',
        choices=list(TEMPLATES.keys()),
        default='dashboard',
        help="Dashboard template to use"
    )
    parser.add_argument(
        '--title',
        default="Interactive Dashboard",
        help="Dashboard title"
    )
    parser.add_argument(
        '--data-source',
        default="data.csv",
        help="Data source file or connection"
    )
    parser.add_argument(
        '--config',
        help="JSON configuration file for advanced customization"
    )
    parser.add_argument(
        '--list-templates',
        action='store_true',
        help="List available templates and exit"
    )

    args = parser.parse_args()

    if args.list_templates:
        print("Available Templates:")
        print("=" * 50)
        for name, template in TEMPLATES.items():
            print(f"  {name:15} - {template.description}")
        return

    # Load configuration
    config = {
        'title': args.title,
        'data_source': args.data_source,
    }

    if args.config:
        try:
            with open(args.config, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)

    # Get template
    template = TEMPLATES.get(args.template)
    if not template:
        print(f"Unknown template: {args.template}")
        sys.exit(1)

    # Generate dashboard
    try:
        dashboard_code = template.generate(config)

        # Ensure output directory exists
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write dashboard file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_code)

        print(f"✅ Dashboard created successfully: {args.output_file}")
        print(f"   Template: {args.template}")
        print(f"   Title: {config['title']}")
        print(f"   Data source: {config['data_source']}")
        print(f"\nTo run the dashboard:")
        print(f"  marimo edit {args.output_file}")
        print(f"  marimo run {args.output_file}")

    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()