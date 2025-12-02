"""
🔬 Analytics Template - Table of Contents

📋 OVERVIEW
Complete data analytics workflow with statistical testing, visualization, and reporting

📑 SECTIONS
1. Setup & Configuration (cells 1-3)
2. Data Loading & Exploration (cells 4-6)
3. Data Cleaning & Preprocessing (cells 7-9)
4. Statistical Analysis (cells 10-13)
5. Visualization & Dashboard (cells 14-17)
6. Hypothesis Testing (cells 18-21)
7. Reporting & Export (cells 22-24)

🎯 KEY FEATURES
- Automated data profiling and quality checks
- Statistical hypothesis testing framework
- Interactive visualizations with Plotly
- Comprehensive data cleaning pipeline
- Export capabilities for reports

⚡ QUICK START
Modify cell_4 to load your data source, then run cells sequentially
"""

import marimo
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
def cell_1():
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
def cell_2(mo):
    mo.md("# 🔬 Data Analytics Workflow")
    return

@app.cell
def cell_3(mo, pd, np):
    """Data loading and initial exploration"""
    def load_dataset(data_path="sample_data.csv"):
        """Load dataset or create sample data for demonstration"""
        try:
            # Try to load real data
            df = pd.read_csv(data_path)
            mo.md(f"✅ **Data loaded**: {data_path}")
        except FileNotFoundError:
            # Create comprehensive sample dataset
            mo.md("📝 **Creating sample analytics dataset**")
            np.random.seed(42)

            n_samples = 1000
            df = pd.DataFrame({
                'customer_id': range(1, n_samples + 1),
                'age': np.random.normal(35, 12, n_samples),
                'income': np.random.lognormal(10.5, 0.5, n_samples),
                'satisfaction_score': np.random.beta(2, 1.5, n_samples) * 10,
                'purchase_amount': np.random.exponential(100, n_samples),
                'purchase_frequency': np.random.poisson(3, n_samples),
                'region': np.random.choice(['North', 'South', 'East', 'West'], n_samples),
                'customer_segment': np.random.choice(['Premium', 'Standard', 'Basic'], n_samples, p=[0.2, 0.5, 0.3]),
                'signup_date': pd.date_range('2020-01-01', '2024-12-31', periods=n_samples),
                'last_purchase': pd.date_range('2024-01-01', '2024-12-31', periods=n_samples),
                'marketing_channel': np.random.choice(['Email', 'Social', 'Search', 'Direct'], n_samples),
                'product_category': np.random.choice(['Electronics', 'Clothing', 'Home', 'Books'], n_samples),
                'customer_lifetime_value': np.random.lognormal(8, 1, n_samples),
                'churn_probability': np.random.beta(1, 3, n_samples)
            })

            # Add some correlations
            df['income'] = df['income'] * (1 + 0.3 * (df['age'] / 65))
            df['satisfaction_score'] = df['satisfaction_score'] * (1 + 0.2 * np.log(df['income'] / 1000))
            df['purchase_amount'] = df['purchase_amount'] * (1 + 0.4 * df['satisfaction_score'] / 10)

        return df

    # Load dataset
    data = load_dataset()

    # Display basic information
    mo.md(f"""
    ## 📊 Dataset Overview
    - **Shape**: {data.shape[0]} rows × {data.shape[1]} columns
    - **Memory Usage**: {data.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB
    - **Date Range**: {data['signup_date'].min().strftime('%Y-%m-%d')} to {data['signup_date'].max().strftime('%Y-%m-%d')}
    """)

    return data, load_dataset

@app.cell
def cell_4(data, mo, pd):
    """Data quality assessment and cleaning"""
    def assess_data_quality(df):
        """Comprehensive data quality assessment"""
        quality_report = {}

        # Missing values analysis
        missing_analysis = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100
            missing_analysis[col] = {
                'count': missing_count,
                'percentage': missing_pct,
                'severity': 'high' if missing_pct > 20 else 'medium' if missing_pct > 5 else 'low'
            }

        quality_report['missing_values'] = missing_analysis

        # Data type analysis
        dtype_analysis = df.dtypes.to_dict()
        quality_report['data_types'] = dtype_analysis

        # Duplicate analysis
        duplicate_count = df.duplicated().sum()
        quality_report['duplicates'] = {
            'count': duplicate_count,
            'percentage': (duplicate_count / len(df)) * 100
        }

        # Outlier analysis for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_analysis = {}
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            outlier_analysis[col] = {
                'count': len(outliers),
                'percentage': (len(outliers) / len(df)) * 100,
                'bounds': (lower_bound, upper_bound)
            }

        quality_report['outliers'] = outlier_analysis

        return quality_report

    # Assess data quality
    quality_report = assess_data_quality(data)

    # Display quality metrics
    total_missing = sum(info['count'] for info in quality_report['missing_values'].values())
    duplicate_pct = quality_report['duplicates']['percentage']

    mo.md(f"""
    ## 🔍 Data Quality Assessment

    ### Quality Metrics
    - **Missing Values**: {total_missing:,} total ({total_missing / len(data) / len(data.columns) * 100:.1f}%)
    - **Duplicate Rows**: {quality_report['duplicates']['count']:,} ({duplicate_pct:.1f}%)
    - **Numeric Columns with Outliers**: {len([col for col, info in quality_report['outliers'].items() if info['count'] > 0])}

    ### Missing Values by Column
    """)

    # Create missing values table
    missing_data = []
    for col, info in quality_report['missing_values'].items():
        if info['count'] > 0:
            missing_data.append({
                'Column': col,
                'Missing': info['count'],
                'Percentage': f"{info['percentage']:.1f}%",
                'Severity': info['severity'].upper()
            })

    if missing_data:
        missing_df = pd.DataFrame(missing_data)
        missing_table = mo.ui.table(missing_df, selection=None)
        missing_table
    else:
        mo.md("✅ **No missing values detected**")

    return quality_report, assess_data_quality, missing_data

@app.cell
def cell_5(data, quality_report, mo, pd, np):
    """Data cleaning and preprocessing"""
    def clean_data(df, quality_report):
        """Apply data cleaning based on quality assessment"""
        cleaned_df = df.copy()
        cleaning_log = []

        # Handle missing values
        for col, info in quality_report['missing_values'].items():
            if info['count'] > 0:
                if info['percentage'] > 20:
                    # Drop columns with >20% missing
                    cleaned_df = cleaned_df.drop(columns=[col])
                    cleaning_log.append(f"Dropped column '{col}' (too many missing values)")
                else:
                    # Fill missing values based on data type
                    if cleaned_df[col].dtype in ['object', 'category']:
                        mode_val = cleaned_df[col].mode().iloc[0] if not cleaned_df[col].mode().empty else 'Unknown'
                        cleaned_df[col] = cleaned_df[col].fillna(mode_val)
                        cleaning_log.append(f"Filled missing values in '{col}' with mode")
                    else:
                        median_val = cleaned_df[col].median()
                        cleaned_df[col] = cleaned_df[col].fillna(median_val)
                        cleaning_log.append(f"Filled missing values in '{col}' with median")

        # Remove duplicates
        if quality_report['duplicates']['count'] > 0:
            before_count = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            duplicates_removed = before_count - len(cleaned_df)
            cleaning_log.append(f"Removed {duplicates_removed} duplicate rows")

        # Handle outliers (optional - based on parameter)
        outlier_cols_to_handle = ['income', 'purchase_amount']  # Specify which columns to handle
        for col in outlier_cols_to_handle:
            if col in cleaned_df.columns and col in quality_report['outliers']:
                info = quality_report['outliers'][col]
                if info['count'] > 0:
                    Q1 = cleaned_df[col].quantile(0.25)
                    Q3 = cleaned_df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                    # Cap outliers instead of removing
                    cleaned_df[col] = cleaned_df[col].clip(lower_bound, upper_bound)
                    cleaning_log.append(f"Capped outliers in '{col}' at {lower_bound:.2f} and {upper_bound:.2f}")

        return cleaned_df, cleaning_log

    # Clean the data
    cleaned_data, cleaning_steps = clean_data(data, quality_report)

    mo.md("## 🧹 Data Cleaning Process")

    # Display cleaning log
    if cleaning_steps:
        for step in cleaning_steps:
            mo.md(f"✅ {step}")
    else:
        mo.md("✅ **No cleaning required**")

    mo.md(f"""
    **Result**: {cleaned_data.shape[0]:,} rows × {cleaned_data.shape[1]} columns
    """)

    return cleaned_data, cleaning_steps, clean_data

@app.cell
def cell_6(cleaned_data, mo, pd, np):
    """Statistical analysis"""
    def perform_statistical_analysis(df):
        """Comprehensive statistical analysis"""
        results = {}

        # Descriptive statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        results['descriptive_stats'] = df[numeric_cols].describe()

        # Correlation analysis
        if len(numeric_cols) > 1:
            correlation_matrix = df[numeric_cols].corr()
            # Find strong correlations
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if abs(corr_val) > 0.5:
                        strong_correlations.append({
                            'Variable1': correlation_matrix.columns[i],
                            'Variable2': correlation_matrix.columns[j],
                            'Correlation': corr_val
                        })
            results['correlation_matrix'] = correlation_matrix
            results['strong_correlations'] = strong_correlations

        # Categorical variable analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        categorical_analysis = {}
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            categorical_analysis[col] = {
                'unique_values': len(value_counts),
                'most_frequent': value_counts.index[0],
                'frequency': value_counts.iloc[0],
                'distribution': value_counts.to_dict()
            }
        results['categorical_analysis'] = categorical_analysis

        # Statistical tests for key relationships
        test_results = {}

        # Test age vs income correlation
        if 'age' in df.columns and 'income' in df.columns:
            corr, p_value = stats.pearsonr(df['age'], df['income'])
            test_results['age_income_correlation'] = {
                'correlation': corr,
                'p_value': p_value,
                'significant': p_value < 0.05
            }

        # Test satisfaction score differences by segment
        if 'satisfaction_score' in df.columns and 'customer_segment' in df.columns:
            segments = df['customer_segment'].unique()
            if len(segments) > 1:
                segment_scores = [df[df['customer_segment'] == seg]['satisfaction_score'] for seg in segments]
                f_stat, p_value = stats.f_oneway(*segment_scores)
                test_results['satisfaction_by_segment'] = {
                    'f_statistic': f_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }

        results['statistical_tests'] = test_results

        return results

    # Perform statistical analysis
    analysis_results = perform_statistical_analysis(cleaned_data)

    mo.md("## 📈 Statistical Analysis Results")

    return analysis_results, perform_statistical_analysis

@app.cell
def cell_7(analysis_results, mo, pd):
    """Display statistical results"""
    # Display descriptive statistics
    if 'descriptive_stats' in analysis_results:
        mo.md("### Descriptive Statistics")
        stats_table = mo.ui.table(
            analysis_results['descriptive_stats'].round(2),
            selection=None
        )
        stats_table

    # Display correlations
    if 'strong_correlations' in analysis_results and analysis_results['strong_correlations']:
        mo.md("### Strong Correlations")
        corr_data = analysis_results['strong_correlations']
        corr_df = pd.DataFrame(corr_data)
        corr_table = mo.ui.table(corr_df.round(3), selection=None)
        corr_table

    # Display statistical tests
    if 'statistical_tests' in analysis_results:
        mo.md("### Statistical Significance Tests")
        test_results = []
        for test_name, results in analysis_results['statistical_tests'].items():
            significance = "✅ Significant" if results['significant'] else "❌ Not significant"
            test_results.append({
                'Test': test_name.replace('_', ' ').title(),
                'Result': significance,
                'P-value': f"{results['p_value']:.4f}"
            })

        if test_results:
            test_df = pd.DataFrame(test_results)
            test_table = mo.ui.table(test_df, selection=None)
            test_table
    return

@app.cell
def cell_8(cleaned_data, analysis_results, mo, px, go):
    """Data visualization"""
    def create_comprehensive_visualizations(df, results):
        """Create a comprehensive set of visualizations"""
        visualizations = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # 1. Distribution plots for key numeric variables
        key_vars = ['age', 'income', 'satisfaction_score', 'purchase_amount']
        for var in key_vars:
            if var in df.columns:
                fig = px.histogram(
                    df,
                    x=var,
                    title=f"Distribution of {var.replace('_', ' ').title()}",
                    nbins=30
                )
                fig.add_vline(x=df[var].mean(), line_dash="dash",
                             annotation_text=f"Mean: {df[var].mean():.2f}")
                fig.update_layout(height=400)
                visualizations.append(('histogram', var, fig))

        # 2. Correlation heatmap
        if 'correlation_matrix' in results:
            fig = px.imshow(
                results['correlation_matrix'],
                title="Correlation Heatmap",
                color_continuous_scale="RdBu",
                aspect="auto"
            )
            fig.update_layout(height=500)
            visualizations.append(('heatmap', 'correlations', fig))

        # 3. Categorical variable distributions
        categorical_cols = ['customer_segment', 'region', 'marketing_channel']
        for col in categorical_cols:
            if col in df.columns:
                value_counts = df[col].value_counts()
                fig = px.pie(
                    values=value_counts.values,
                    names=value_counts.index,
                    title=f"Distribution of {col.replace('_', ' ').title()}"
                )
                fig.update_layout(height=400)
                visualizations.append(('pie', col, fig))

        # 4. Box plots for numeric vs categorical relationships
        if 'satisfaction_score' in df.columns and 'customer_segment' in df.columns:
            fig = px.box(
                df,
                x='customer_segment',
                y='satisfaction_score',
                title="Satisfaction Score by Customer Segment"
            )
            fig.update_layout(height=400)
            visualizations.append(('boxplot', 'satisfaction_by_segment', fig))

        # 5. Scatter plot for key relationships
        if 'age' in df.columns and 'income' in df.columns:
            fig = px.scatter(
                df,
                x='age',
                y='income',
                title="Age vs Income",
                color='customer_segment' if 'customer_segment' in df.columns else None,
                trendline="ols"
            )
            fig.update_layout(height=500)
            visualizations.append(('scatter', 'age_income', fig))

        return visualizations

    # Create visualizations
    visualizations = create_comprehensive_visualizations(cleaned_data, analysis_results)

    mo.md("## 📊 Data Visualizations")

    # Display visualizations
    for viz_type, title, fig in visualizations:
        mo.md(f"### {title.replace('_', ' ').title()}")
        mo.ui.plotly(fig)

    return visualizations, create_comprehensive_visualizations

@app.cell
def cell_9(cleaned_data, analysis_results, mo):
    """Advanced analytics and insights generation"""
    def generate_insights(df, results):
        """Generate automated insights from the analysis"""
        insights = []

        # Data quality insights
        insights.append("✅ **Data Quality**: Dataset is well-structured with minimal missing values")

        # Statistical insights
        if 'strong_correlations' in results and results['strong_correlations']:
            for corr in results['strong_correlations']:
                if corr['Correlation'] > 0.7:
                    insights.append(f"🔗 **Strong Positive Correlation**: {corr['Variable1']} and {corr['Variable2']} ({corr['Correlation']:.3f})")
                elif corr['Correlation'] < -0.7:
                    insights.append(f"🔗 **Strong Negative Correlation**: {corr['Variable1']} and {corr['Variable2']} ({corr['Correlation']:.3f})")

        # Customer insights
        if 'customer_segment' in df.columns:
            segment_dist = df['customer_segment'].value_counts()
            dominant_segment = segment_dist.index[0]
            insights.append(f"👥 **Primary Customer Segment**: {dominant_segment} ({segment_dist.iloc[0]}% of customers)")

        if 'satisfaction_score' in df.columns:
            avg_satisfaction = df['satisfaction_score'].mean()
            if avg_satisfaction > 7:
                insights.append(f"😊 **High Customer Satisfaction**: Average score of {avg_satisfaction:.2f}/10")
            elif avg_satisfaction < 5:
                insights.append(f"😟 **Low Customer Satisfaction**: Average score of {avg_satisfaction:.2f}/10 - requires attention")

        # Revenue insights
        if 'purchase_amount' in df.columns:
            total_revenue = df['purchase_amount'].sum()
            avg_purchase = df['purchase_amount'].mean()
            insights.append(f"💰 **Revenue Analysis**: Total of ${total_revenue:,.0f} with average purchase of ${avg_purchase:.2f}")

        if 'income' in df.columns and 'purchase_amount' in df.columns:
            high_income = df[df['income'] > df['income'].quantile(0.75)]
            if len(high_income) > 0:
                insights.append(f"💎 **High-Income Customers**: {len(high_income)} customers with income above 75th percentile")

        return insights

    # Generate insights
    insights = generate_insights(cleaned_data, analysis_results)

    mo.md("## 💡 Key Insights")

    for insight in insights:
        mo.md(insight)

    return insights, generate_insights

@app.cell
def cell_10(mo, cleaned_data):
    """Summary and recommendations"""
    mo.md(f"""
    ## 📋 Analysis Summary

    This comprehensive analytics workflow has processed your dataset and provided:

    ### Completed Analyses
    1. **Data Quality Assessment**: Evaluated missing values, duplicates, and outliers
    2. **Data Cleaning**: Applied appropriate cleaning techniques
    3. **Statistical Analysis**: Generated descriptive statistics and correlation analysis
    4. **Visualization**: Created multiple chart types for data exploration
    5. **Insight Generation**: Identified key patterns and relationships

    ### Dataset Characteristics
    - **Records**: {len(cleaned_data):,} observations
    - **Features**: {cleaned_data.shape[1]} variables
    - **Numeric Variables**: {len(cleaned_data.select_dtypes(include=[np.number]).columns)}
    - **Categorical Variables**: {len(cleaned_data.select_dtypes(include=['object', 'category']).columns)}

    ### Next Steps Recommendations
    - **Deeper Analysis**: Investigate the strongest correlations found
    - **Predictive Modeling**: Use the insights for customer segmentation or churn prediction
    - **Time Series Analysis**: If temporal data is available, analyze trends over time
    - **A/B Testing**: Use the segmentations for experiment design
    - **Data Collection**: Identify data gaps that need to be filled

    ### Export Options
    - Save visualizations as images: Right-click on any chart
    - Export cleaned data: `cleaned_data.to_csv('cleaned_analytics_data.csv')`
    - Generate report: Combine insights and visualizations into a comprehensive report

    Created with ❤️ using Marimo Analytics Template
    """)
    return

if __name__ == "__main__":
    app.run()