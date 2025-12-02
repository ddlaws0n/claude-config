import marimo
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def cell_1():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    from datetime import datetime, timedelta
    return mo, pd, px, datetime, timedelta

@app.cell
def cell_2(mo):
    mo.md("# 📊 Interactive Dashboard Template")
    return

@app.cell
def cell_3(mo, pd):
    """Data loading with sample data generation"""
    def load_sample_data():
        """Generate sample business data for demonstration"""
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')

        data = []
        for date in dates:
            base_revenue = 1000 + (date.dayofyear * 2)
            daily_variation = (hash(str(date)) % 200) - 100

            data.append({
                'date': date,
                'revenue': base_revenue + daily_variation,
                'users': 100 + (date.dayofyear) + (hash(str(date)) % 50),
                'page_views': 500 + (date.dayofyear * 3) + (hash(str(date)) % 200),
                'conversion_rate': max(0.01, min(0.15, 0.05 + (hash(str(date)) % 100) / 1000)),
                'segment': ['desktop', 'mobile', 'tablet'][date.dayofyear % 3],
                'region': ['US', 'EU', 'APAC', 'LATAM'][date.dayofyear % 4]
            })

        return pd.DataFrame(data)

    # Load data
    df = load_sample_data()

    mo.md(f"📈 **Dataset Loaded**: {df.shape[0]:,} rows, {df.shape[1]} columns")
    return df, load_sample_data

@app.cell
def cell_4(df, mo):
    """Interactive controls"""
    # Date range filter
    date_filter = mo.ui.date_range(
        start=df['date'].min().date(),
        stop=df['date'].max().date(),
        value=(df['date'].min().date(), df['date'].max().date()),
        label="Date Range"
    )

    # Metric selector
    metric_selector = mo.ui.dropdown(
        options=['revenue', 'users', 'page_views', 'conversion_rate'],
        value='revenue',
        label="Primary Metric"
    )

    # Segment filter
    segment_filter = mo.ui.multiselect(
        options=['all'] + list(df['segment'].unique()),
        value=['all'],
        label="Segment"
    )

    # Region filter
    region_filter = mo.ui.multiselect(
        options=['all'] + list(df['region'].unique()),
        value=['all'],
        label="Region"
    )

    # Chart type selector
    chart_type = mo.ui.dropdown(
        options=['line', 'bar', 'area', 'scatter'],
        value='line',
        label="Chart Type"
    )

    controls = mo.ui.dictionary({
        'date_range': date_filter,
        'metric': metric_selector,
        'segment': segment_filter,
        'region': region_filter,
        'chart_type': chart_type
    })

    mo.md("## 🎛️ Dashboard Controls")
    controls
    return date_filter, metric_selector, segment_filter, region_filter, chart_type, controls

@app.cell
def cell_5(df, controls, mo, px):
    """Data filtering and processing"""
    def filter_data(data, controls_value):
        """Apply filters to the data"""
        filtered_df = data.copy()

        # Date filter
        start_date, end_date = controls_value['date_range'].value
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= start_date) &
            (filtered_df['date'].dt.date <= end_date)
        ]

        # Segment filter
        if 'all' not in controls_value['segment'].value:
            filtered_df = filtered_df[
                filtered_df['segment'].isin(controls_value['segment'].value)
            ]

        # Region filter
        if 'all' not in controls_value['region'].value:
            filtered_df = filtered_df[
                filtered_df['region'].isin(controls_value['region'].value)
            ]

        return filtered_df

    # Apply filters
    filtered_data = filter_data(df, controls.value)

    # Calculate summary statistics
    summary_stats = {
        'total_revenue': f"${filtered_data['revenue'].sum():,.0f}",
        'avg_users': f"{filtered_data['users'].mean():.0f}",
        'conversion_rate': f"{filtered_data['conversion_rate'].mean():.2%}",
        'date_range': f"{len(filtered_data)} days"
    }

    return filter_data, filtered_data, summary_stats

@app.cell
def cell_6(filtered_data, controls, mo, px):
    """Main visualization"""
    def create_chart(data, controls_value):
        """Create the main chart based on selections"""
        if data.empty:
            return mo.md("No data available for selected filters")

        chart_type = controls_value['chart_type'].value
        metric = controls_value['metric'].value

        # Create chart based on type
        if chart_type == 'line':
            fig = px.line(
                data,
                x='date',
                y=metric,
                title=f"{metric.replace('_', ' ').title()} Over Time",
                color='segment' if 'segment' in data.columns else None
            )
        elif chart_type == 'bar':
            # Group by month for bar chart
            data['month'] = data['date'].dt.to_period('M').dt.to_timestamp()
            monthly_data = data.groupby('month')[metric].sum().reset_index()

            fig = px.bar(
                monthly_data,
                x='month',
                y=metric,
                title=f"Monthly {metric.replace('_', ' ').title()}"
            )
        elif chart_type == 'area':
            fig = px.area(
                data,
                x='date',
                y=metric,
                title=f"{metric.replace('_', ' ').title()} Over Time",
                color='segment' if 'segment' in data.columns else None
            )
        else:  # scatter
            numeric_cols = data.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                fig = px.scatter(
                    data,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    color='segment' if 'segment' in data.columns else None
                )
            else:
                fig = px.line(
                    data,
                    x='date',
                    y=metric,
                    title=f"{metric.replace('_', ' ').title()} Over Time"
                )

        # Update layout
        fig.update_layout(
            height=500,
            template="plotly_white",
            showlegend=True
        )

        return mo.ui.plotly(fig)

    # Create chart
    main_chart = create_chart(filtered_data, controls.value)

    mo.md("## 📈 Primary Visualization")
    main_chart
    return main_chart, create_chart

@app.cell
def cell_7(filtered_data, mo):
    """Summary statistics display"""
    # Create KPI cards
    kpi_data = [
        ("💰", "Total Revenue", summary_stats['total_revenue']),
        ("👥", "Avg Users", summary_stats['avg_users']),
        ("📈", "Conversion Rate", summary_stats['conversion_rate']),
        ("📅", "Date Range", summary_stats['date_range'])
    ]

    kpi_cards = []
    for icon, title, value in kpi_data:
        kpi_html = f"""
        <div style='padding: 1rem; border: 1px solid #e0e0e0; border-radius: 8px; text-align: center; background: white;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>{icon}</div>
            <div style='font-weight: bold; color: #333; margin-bottom: 0.5rem;'>{title}</div>
            <div style='font-size: 1.25rem; color: #666;'>{value}</div>
        </div>
        """
        kpi_cards.append(kpi_html)

    kpi_grid = f"""
    <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;'>
        {''.join(kpi_cards)}
    </div>
    """

    mo.md("## 📊 Key Performance Indicators")
    mo.md(kpi_grid)
    return kpi_data, kpi_cards, kpi_grid

@app.cell
def cell_8(filtered_data, mo, px):
    """Secondary visualizations"""
    # Segment breakdown
    segment_chart = None
    if 'segment' in filtered_data.columns:
        segment_summary = filtered_data.groupby('segment')['revenue'].sum().reset_index()

        fig_segment = px.pie(
            segment_summary,
            values='revenue',
            names='segment',
            title="Revenue by Segment"
        )
        fig_segment.update_layout(height=300)
        segment_chart = mo.ui.plotly(fig_segment)

    # Region breakdown
    region_chart = None
    if 'region' in filtered_data.columns:
        region_summary = filtered_data.groupby('region')['users'].sum().reset_index()

        fig_region = px.bar(
            region_summary,
            x='region',
            y='users',
            title="Users by Region"
        )
        fig_region.update_layout(height=300)
        region_chart = mo.ui.plotly(fig_region)

    # Conversion trend
    conversion_chart = None
    if 'conversion_rate' in filtered_data.columns:
        # Weekly average conversion rate
        filtered_data['week'] = filtered_data['date'].dt.isocalendar().week
        weekly_conversion = filtered_data.groupby('week')['conversion_rate'].mean().reset_index()

        fig_conversion = px.line(
            weekly_conversion,
            x='week',
            y='conversion_rate',
            title="Weekly Conversion Rate Trend"
        )
        fig_conversion.update_layout(height=300)
        conversion_chart = mo.ui.plotly(fig_conversion)

    mo.md("## 📊 Secondary Analytics")

    # Display charts if available
    if segment_chart:
        mo.md("### Segment Performance")
        segment_chart

    if region_chart:
        mo.md("### Regional Distribution")
        region_chart

    if conversion_chart:
        mo.md("### Conversion Trends")
        conversion_chart
    return segment_chart, region_chart, conversion_chart

@app.cell
def cell_9(mo):
    """Instructions and customization guide"""
    mo.md("""
    ## 🛠️ Customization Guide

    This dashboard template provides:

    ### Features
    - **Interactive filtering** by date, segment, and region
    - **Multiple chart types** (line, bar, area, scatter)
    - **Key performance indicators** with real-time updates
    - **Secondary analytics** for deeper insights
    - **Responsive design** that works on all devices

    ### How to Customize
    1. **Replace sample data**: Modify the `load_sample_data()` function to load your real data
    2. **Add new metrics**: Update the `metric_selector` options
    3. **Change visualizations**: Modify the `create_chart()` function
    4. **Add filters**: Extend the controls dictionary with new UI elements
    5. **Customize styling**: Modify the HTML templates for KPI cards

    ### Data Requirements
    - Data should have a date column
    - Numeric columns for metrics
    - Optional categorical columns for segmentation
    - Pandas DataFrame format

    ### Extension Ideas
    - Add export functionality for charts
    - Implement real-time data updates
    - Add drill-down capabilities
    - Integrate with external APIs
    - Add user authentication and permissions

    Created with ❤️ using Marimo Dashboard Template
    """)
    return

if __name__ == "__main__":
    app.run()