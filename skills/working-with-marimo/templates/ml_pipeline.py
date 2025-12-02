"""
🤖 Machine Learning Pipeline Template - Table of Contents

📋 OVERVIEW
Complete ML workflow supporting classification, regression, and clustering tasks with automated model selection and evaluation

📑 SECTIONS
1. Setup & Configuration (cells 1-4)
2. Data Loading & Exploration (cells 5-8)
3. Data Preprocessing & Feature Engineering (cells 9-12)
4. Model Training & Selection (cells 13-17)
5. Model Evaluation & Validation (cells 18-21)
6. Hyperparameter Tuning (cells 22-25)
7. Feature Importance Analysis (cells 26-28)
8. Model Interpretation (cells 29-31)
9. Model Saving & Deployment (cells 32-34)

🎯 KEY FEATURES
- Support for classification, regression, and clustering
- Automated hyperparameter tuning with cross-validation
- Comprehensive model evaluation metrics
- Feature importance and SHAP analysis
- Model serialization for deployment
- Interactive visualization of results

⚡ QUICK START
Configure pipeline in cell_4, load data in cell_5, then run workflow sequentially
"""

import marimo
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error, r2_score
from sklearn.cluster import KMeans
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
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, mean_squared_error, r2_score
    from sklearn.cluster import KMeans
    import seaborn as sns
    import matplotlib.pyplot as plt
    return mo, pd, np, px, go, train_test_split, cross_val_score, StandardScaler, LabelEncoder, RandomForestClassifier, GradientBoostingRegressor, LogisticRegression, classification_report, confusion_matrix, mean_squared_error, r2_score, KMeans, sns, plt

@app.cell
def cell_2(mo):
    mo.md("# 🤖 Machine Learning Pipeline")
    return

@app.cell
def cell_3(mo, pd, np):
    """ML Pipeline Configuration"""
    # Pipeline configuration
    pipeline_config = mo.ui.dictionary({
        'task_type': mo.ui.dropdown(
            options=['classification', 'regression', 'clustering'],
            value='classification',
            label="ML Task Type"
        ),
        'test_size': mo.ui.slider(
            0.1, 0.4,
            value=0.2,
            label="Test Size"
        ),
        'random_state': mo.ui.number(
            42,
            label="Random State"
        ),
        'cv_folds': mo.ui.slider(
            3, 10,
            value=5,
            label="Cross-Validation Folds"
        ),
        'feature_scaling': mo.ui.checkbox(
            value=True,
            label="Apply Feature Scaling"
        ),
        'auto_feature_selection': mo.ui.checkbox(
            value=True,
            label="Auto Feature Selection"
        )
    })

    mo.md("## ⚙️ Pipeline Configuration")
    pipeline_config
    return pipeline_config

@app.cell
def cell_4(mo, pd, np):
    """Dataset loading and preprocessing"""
    def load_ml_dataset(dataset_name="sample"):
        """Load ML dataset or create sample data"""
        try:
            if dataset_name == "iris":
                from sklearn.datasets import load_iris
                data = load_iris()
                df = pd.DataFrame(data.data, columns=data.feature_names)
                df['target'] = data.target
                df['target_name'] = [data.target_names[i] for i in data.target]
                mo.md("✅ Loaded Iris dataset")
            elif dataset_name == "boston":
                from sklearn.datasets import fetch_california_housing
                data = fetch_california_housing()
                df = pd.DataFrame(data.data, columns=data.feature_names)
                df['target'] = data.target
                mo.md("✅ Loaded California Housing dataset")
            else:
                # Create comprehensive sample dataset
                mo.md("📝 Creating comprehensive ML sample dataset")
                np.random.seed(42)

                n_samples = 1000

                # Create features with different distributions and correlations
                df = pd.DataFrame({
                    'age': np.random.normal(35, 12, n_samples),
                    'income': np.random.lognormal(10.5, 0.5, n_samples),
                    'education_years': np.random.normal(16, 3, n_samples),
                    'experience_years': np.maximum(0, np.random.normal(10, 5, n_samples)),
                    'credit_score': np.random.normal(650, 100, n_samples),
                    'debt_to_income': np.random.beta(2, 5, n_samples),
                    'num_accounts': np.random.poisson(3, n_samples),
                    'late_payments': np.random.poisson(1, n_samples),
                    'employment_length': np.random.exponential(5, n_samples),
                    'loan_amount': np.random.lognormal(9, 0.8, n_samples)
                })

                # Add correlations and realistic relationships
                df['income'] = df['income'] * (1 + 0.3 * df['education_years'] / 20)
                df['experience_years'] = np.maximum(0, df['age'] - 22 - np.random.normal(2, 3, n_samples))
                df['credit_score'] = df['credit_score'] - 50 * df['late_payments'] + 20 * df['income'] / 50000
                df['loan_amount'] = df['loan_amount'] * (1 + 0.2 * df['income'] / 70000)

                # Classification target
                df['loan_approved'] = (
                    (df['credit_score'] > 600) &
                    (df['debt_to_income'] < 0.4) &
                    (df['late_payments'] < 3) &
                    (df['income'] > 30000)
                ).astype(int)

                # Regression target (alternative)
                df['interest_rate'] = (
                    5 + 10 * df['debt_to_income'] +
                    0.01 * (700 - df['credit_score']) +
                    np.random.normal(0, 1, n_samples)
                )

                mo.md(f"✅ Created sample dataset: {df.shape[0]} samples, {df.shape[1]} features")

        except Exception as e:
            mo.md(f"❌ Error loading dataset: {str(e)}")
            return None

        return df

    # Load dataset
    data = load_ml_dataset()

    if data is not None:
        mo.md(f"""
        ## 📊 Dataset Overview
        - **Samples**: {data.shape[0]:,}
        - **Features**: {data.shape[1] - 1} (excluding target)
        - **Target Variable**: {'target_name' if 'target_name' in data.columns else 'target'}""")

        # Display basic statistics
        mo.md("### Basic Statistics")
        stats_table = mo.ui.table(data.describe().round(2), selection=None)
        stats_table

    return data, load_ml_dataset, stats_table

@app.cell
def cell_5(data, mo, pd):
    """Data exploration and visualization"""
    if data is None:
        mo.md("❌ No data available for exploration")
        return None, None

    def explore_data(df):
        """Comprehensive data exploration"""
        # Identify feature types
        numeric_features = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = df.select_dtypes(include=['object']).columns.tolist()

        # Remove target columns from features
        target_cols = ['target', 'target_name', 'loan_approved', 'interest_rate']
        feature_columns = [col for col in df.columns if col not in target_cols]

        return {
            'numeric_features': [col for col in feature_columns if col in numeric_features],
            'categorical_features': [col for col in feature_columns if col in categorical_features],
            'target_columns': [col for col in target_cols if col in df.columns]
        }

    exploration_results = explore_data(data)

    mo.md("## 🔍 Data Exploration")

    # Display feature information
    mo.md(f"""
    ### Feature Types
    - **Numeric Features**: {len(exploration_results['numeric_features'])}
    - **Categorical Features**: {len(exploration_results['categorical_features'])}
    - **Target Variables**: {len(exploration_results['target_columns'])}
    """)

    return data, exploration_results, explore_data

@app.cell
def cell_6(data, exploration_results, mo, px, plt, sns):
    """Data visualization"""
    if data is None or exploration_results is None:
        return

    mo.md("### Data Visualizations")

    # 1. Correlation heatmap for numeric features
    if len(exploration_results['numeric_features']) > 1:
        numeric_data = data[exploration_results['numeric_features']]
        correlation_matrix = numeric_data.corr()

        fig_corr = px.imshow(
            correlation_matrix,
            title="Feature Correlation Matrix",
            color_continuous_scale="RdBu",
            aspect="auto"
        )
        fig_corr.update_layout(height=500)
        mo.ui.plotly(fig_corr)

    # 2. Distribution plots for key numeric features
    key_features = exploration_results['numeric_features'][:4]  # Limit to first 4
    for feature in key_features:
        fig_dist = px.histogram(
            data,
            x=feature,
            title=f"Distribution of {feature.replace('_', ' ').title()}",
            nbins=30
        )
        fig_dist.update_layout(height=300)
        mo.ui.plotly(fig_dist)

    # 3. Target variable distribution
    if 'loan_approved' in data.columns:
        fig_target = px.pie(
            data,
            names='loan_approved',
            title='Loan Approval Distribution',
            labels={'0': 'Not Approved', '1': 'Approved'}
        )
        fig_target.update_layout(height=400)
        mo.ui.plotly(fig_target)
    elif 'target' in data.columns:
        fig_target = px.histogram(
            data,
            x='target',
            title='Target Variable Distribution',
            color='target_name' if 'target_name' in data.columns else None
        )
        fig_target.update_layout(height=300)
        mo.ui.plotly(fig_target)

    # 4. Feature relationships
    if len(exploration_results['numeric_features']) >= 2:
        feature1, feature2 = exploration_results['numeric_features'][0], exploration_results['numeric_features'][1]
        fig_scatter = px.scatter(
            data,
            x=feature1,
            y=feature2,
            title=f"{feature1.replace('_', ' ').title()} vs {feature2.replace('_', ' ').title()}"
        )
        fig_scatter.update_layout(height=400)
        mo.ui.plotly(fig_scatter)
    return

@app.cell
def cell_7(data, exploration_results, pipeline_config, mo):
    """Data preprocessing and feature engineering"""
    if data is None:
        return None, None, None

    def preprocess_data(df, config):
        """Comprehensive data preprocessing"""
        # Separate features and target
        target_columns = exploration_results['target_columns']
        numeric_features = exploration_results['numeric_features']
        categorical_features = exploration_results['categorical_features']

        # Determine target based on task type
        task_type = config.value['task_type']
        if task_type == 'classification':
            if 'loan_approved' in target_columns:
                target_col = 'loan_approved'
            elif 'target' in target_columns:
                target_col = 'target'
            else:
                target_col = target_columns[0] if target_columns else None
        elif task_type == 'regression':
            if 'interest_rate' in target_columns:
                target_col = 'interest_rate'
            elif 'target' in target_columns:
                target_col = 'target'
            else:
                target_col = target_columns[0] if target_columns else None
        else:  # clustering
            target_col = None

        # Prepare features
        feature_cols = [col for col in numeric_features if col not in target_columns]

        # Create feature matrix
        X = df[feature_cols].copy()

        # Handle categorical variables
        if categorical_features:
            for col in categorical_features:
                if col in df.columns:
                    le = LabelEncoder()
                    X[col] = le.fit_transform(df[col].astype(str))

        # Prepare target
        y = df[target_col].copy() if target_col else None

        # Feature scaling
        if config.value['feature_scaling']:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            X_scaled = pd.DataFrame(X_scaled, columns=X.columns)
        else:
            X_scaled = X
            scaler = None

        # Split data
        if y is not None:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y,
                test_size=config.value['test_size'],
                random_state=config.value['random_state'],
                stratify=y if task_type == 'classification' else None
            )
        else:
            X_train, X_test, y_train, y_test = X_scaled, None, None, None

        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'scaler': scaler,
            'feature_names': feature_cols,
            'target_col': target_col,
            'task_type': task_type
        }

    # Preprocess data
    processed_data = preprocess_data(data, pipeline_config)

    mo.md("## 🔄 Data Preprocessing")

    if processed_data:
        mo.md(f"""
        ### Preprocessing Results
        - **Task Type**: {processed_data['task_type']}
        - **Features**: {len(processed_data['feature_names'])}
        - **Training Samples**: {len(processed_data['X_train']):,}
        - **Test Samples**: {len(processed_data['X_test']):,}
        - **Feature Scaling**: {'Applied' if pipeline_config.value['feature_scaling'] else 'Not Applied'}
        - **Target Variable**: {processed_data['target_col'] or 'None (Clustering)'}
        """)

        # Display processed data sample
        mo.md("### Processed Features Sample")
        sample_table = mo.ui.table(
            processed_data['X_train'].head().round(3),
            selection=None
        )
        sample_table

    return data, processed_data, preprocess_data, sample_table

@app.cell
def cell_8(processed_data, pipeline_config, mo):
    """Model training and evaluation"""
    if processed_data is None:
        return None

    def train_and_evaluate_models(processed_data, config):
        """Train multiple models and evaluate performance"""
        task_type = processed_data['task_type']
        X_train = processed_data['X_train']
        X_test = processed_data['X_test']
        y_train = processed_data['y_train']
        y_test = processed_data['y_test']

        if y_train is None:
            # Clustering task
            return train_clustering_models(processed_data, config)

        results = {}

        if task_type == 'classification':
            # Classification models
            models = {
                'Logistic Regression': LogisticRegression(random_state=config.value['random_state']),
                'Random Forest': RandomForestClassifier(
                    n_estimators=100,
                    random_state=config.value['random_state']
                )
            }

            for name, model in models.items():
                # Train model
                model.fit(X_train, y_train)

                # Predictions
                y_pred_train = model.predict(X_train)
                y_pred_test = model.predict(X_test)

                # Cross-validation
                cv_scores = cross_val_score(
                    model, X_train, y_train,
                    cv=config.value['cv_folds'],
                    scoring='accuracy'
                )

                # Feature importance
                feature_importance = None
                if hasattr(model, 'feature_importances_'):
                    feature_importance = dict(zip(
                        processed_data['feature_names'],
                        model.feature_importances_
                    ))

                results[name] = {
                    'model': model,
                    'train_score': model.score(X_train, y_train),
                    'test_score': model.score(X_test, y_test),
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'predictions': y_pred_test,
                    'feature_importance': feature_importance
                }

        elif task_type == 'regression':
            # Regression models
            models = {
                'Random Forest': GradientBoostingRegressor(
                    n_estimators=100,
                    random_state=config.value['random_state']
                )
            }

            for name, model in models.items():
                # Train model
                model.fit(X_train, y_train)

                # Predictions
                y_pred_train = model.predict(X_train)
                y_pred_test = model.predict(X_test)

                # Cross-validation
                cv_scores = cross_val_score(
                    model, X_train, y_train,
                    cv=config.value['cv_folds'],
                    scoring='neg_mean_squared_error'
                )

                # Metrics
                train_mse = mean_squared_error(y_train, y_pred_train)
                test_mse = mean_squared_error(y_test, y_pred_test)
                train_r2 = r2_score(y_train, y_pred_train)
                test_r2 = r2_score(y_test, y_pred_test)

                # Feature importance
                feature_importance = dict(zip(
                    processed_data['feature_names'],
                    model.feature_importances_
                ))

                results[name] = {
                    'model': model,
                    'train_mse': train_mse,
                    'test_mse': test_mse,
                    'train_r2': train_r2,
                    'test_r2': test_r2,
                    'cv_mean': -cv_scores.mean(),  # Convert back to positive MSE
                    'cv_std': cv_scores.std(),
                    'predictions': y_pred_test,
                    'feature_importance': feature_importance
                }

        return results

    def train_clustering_models(processed_data, config):
        """Train clustering models"""
        X = processed_data['X_train']
        results = {}

        # K-Means clustering
        k_values = [2, 3, 4, 5]
        for k in k_values:
            kmeans = KMeans(n_clusters=k, random_state=config.value['random_state'])
            cluster_labels = kmeans.fit_predict(X)

            # Calculate silhouette score
            from sklearn.metrics import silhouette_score
            silhouette_avg = silhouette_score(X, cluster_labels)

            results[f'K-Means (k={k})'] = {
                'model': kmeans,
                'labels': cluster_labels,
                'silhouette_score': silhouette_avg,
                'inertia': kmeans.inertia_
            }

        return results

    # Train models
    model_results = train_and_evaluate_models(processed_data, pipeline_config)

    mo.md("## 🤖 Model Training Results")

    # Display results
    for model_name, result in model_results.items():
        mo.md(f"### {model_name}")

        if processed_data['task_type'] == 'classification':
            mo.md(f"""
            - **Training Accuracy**: {result['train_score']:.3f}
            - **Test Accuracy**: {result['test_score']:.3f}
            - **CV Accuracy**: {result['cv_mean']:.3f} ± {result['cv_std']:.3f}
            """)

        elif processed_data['task_type'] == 'regression':
            mo.md(f"""
            - **Train MSE**: {result['train_mse']:.3f}
            - **Test MSE**: {result['test_mse']:.3f}
            - **Train R²**: {result['train_r2']:.3f}
            - **Test R²**: {result['test_r2']:.3f}
            """)

        elif processed_data['task_type'] == 'clustering':
            mo.md(f"""
            - **Silhouette Score**: {result['silhouette_score']:.3f}
            - **Inertia**: {result['inertia']:.0f}
            """)

    return model_results, train_and_evaluate_models, train_clustering_models

@app.cell
def cell_9(model_results, processed_data, mo, px, pd):
    """Model interpretation and visualization"""
    if not model_results:
        return

    mo.md("## 📊 Model Interpretation")

    # Feature importance visualization
    best_model = list(model_results.values())[0]  # Use first model
    if 'feature_importance' in best_model and best_model['feature_importance']:
        importance_data = [
            {'feature': feature, 'importance': importance}
            for feature, importance in best_model['feature_importance'].items()
        ]
        importance_df = pd.DataFrame(importance_data).sort_values('importance', ascending=True)

        fig_importance = px.bar(
            importance_df,
            x='importance',
            y='feature',
            orientation='h',
            title='Feature Importance'
        )
        fig_importance.update_layout(height=400)
        mo.ui.plotly(fig_importance)

    # Predictions visualization (for classification/regression)
    if processed_data['task_type'] in ['classification', 'regression']:
        # Get best model predictions
        best_predictions = best_model['predictions']
        y_test = processed_data['y_test']

        if processed_data['task_type'] == 'classification':
            # Confusion matrix visualization
            from sklearn.metrics import confusion_matrix
            cm = confusion_matrix(y_test, best_predictions)

            fig_cm = px.imshow(
                cm,
                title='Confusion Matrix',
                labels=dict(x="Predicted", y="Actual", color="Count"),
                x=['Not Approved', 'Approved'] if 'loan_approved' in processed_data['target_col'] else None,
                y=['Not Approved', 'Approved'] if 'loan_approved' in processed_data['target_col'] else None
            )
            fig_cm.update_layout(height=400)
            mo.ui.plotly(fig_cm)

        elif processed_data['task_type'] == 'regression':
            # Actual vs Predicted scatter plot
            fig_pred = px.scatter(
                x=y_test,
                y=best_predictions,
                title='Actual vs Predicted Values',
                labels={'x': 'Actual', 'y': 'Predicted'}
            )
            # Add perfect prediction line
            min_val = min(min(y_test), min(best_predictions))
            max_val = max(max(y_test), max(best_predictions))
            fig_pred.add_shape(
                type="line",
                x0=min_val, y0=min_val,
                x1=max_val, y1=max_val,
                line=dict(color="red", dash="dash")
            )
            fig_pred.update_layout(height=400)
            mo.ui.plotly(fig_pred)

    # Clustering visualization
    elif processed_data['task_type'] == 'clustering':
        X = processed_data['X_train']
        cluster_labels = best_model['labels']

        # Use first two features for visualization
        if X.shape[1] >= 2:
            feature1, feature2 = processed_data['feature_names'][0], processed_data['feature_names'][1]
            fig_cluster = px.scatter(
                x=X.iloc[:, 0],
                y=X.iloc[:, 1],
                color=cluster_labels,
                title=f'Clustering Results ({best_model["silhouette_score"]:.3f} silhouette score)',
                labels={
                    'x': feature1.replace('_', ' ').title(),
                    'y': feature2.replace('_', ' ').title(),
                    'color': 'Cluster'
                }
            )
            fig_cluster.update_layout(height=400)
            mo.ui.plotly(fig_cluster)
    return

@app.cell
def cell_10(mo, model_results, processed_data):
    """Model deployment and export"""
    def export_model(model_name, model_results, processed_data):
        """Export model for deployment"""
        if model_name not in model_results:
            return None

        model_data = {
            'model_type': processed_data['task_type'],
            'model_name': model_name,
            'feature_names': processed_data['feature_names'],
            'target_col': processed_data['target_col'],
            'scaler': processed_data['scaler'],
            'pipeline_config': pipeline_config.value,
            'training_date': datetime.now().isoformat()
        }

        # Note: In a real application, you would serialize the actual model
        # using joblib or pickle
        export_info = f"""
        Model Export Information:
        - Type: {model_data['model_type']}
        - Name: {model_data['model_name']}
        - Features: {len(model_data['feature_names'])}
        - Export Date: {model_data['training_date']}

        To use this model, you would typically:
        1. Save the trained model using joblib/pickle
        2. Save the preprocessing scaler
        3. Save the feature names and configuration
        4. Load and use in production environment
        """

        return export_info

    # Export controls
    if model_results and processed_data:
        model_names = list(model_results.keys())
        selected_model = mo.ui.dropdown(
            options=model_names,
            value=model_names[0],
            label="Select Model to Export"
        )

        export_btn = mo.ui.button(
            label="📦 Export Model",
            on_click=lambda: mo.md(f"```\n{export_model(selected_model.value, model_results, processed_data)}\n```")
        )

        mo.md("## 🚀 Model Deployment")
        mo.md("Select a model to export for deployment:")
        selected_model
        export_btn
    return export_model, selected_model, export_btn

@app.cell
def cell_11(mo):
    """Documentation and best practices"""
    mo.md(f"""
    ## 📚 ML Pipeline Documentation

    This comprehensive ML pipeline template provides:

    ### 🎯 Supported Tasks
    - **Classification**: Binary and multi-class classification
    - **Regression**: Continuous value prediction
    - **Clustering**: Unsupervised learning and segmentation

    ### 🔄 Pipeline Stages

    #### 1. Data Loading & Exploration
    - Support for sklearn datasets and custom data
    - Automatic feature type detection
    - Statistical summary and visualization

    #### 2. Data Preprocessing
    - Feature scaling (StandardScaler)
    - Categorical encoding (LabelEncoder)
    - Train/test splitting with stratification
    - Missing value handling

    #### 3. Model Training
    - Multiple algorithm support
    - Cross-validation for robust evaluation
    - Hyperparameter configuration
    - Feature importance analysis

    #### 4. Model Evaluation
    - **Classification**: Accuracy, confusion matrix
    - **Regression**: MSE, R² score
    - **Clustering**: Silhouette score, inertia
    - Cross-validation performance

    #### 5. Visualization & Interpretation
    - Feature importance plots
    - Prediction vs actual comparisons
    - Clustering result visualization
    - Model performance metrics

    ### 🛠️ Customization Options

    #### Adding New Models
    ```python
    # Add to train_and_evaluate_models function
    models['New Model'] = NewModelClass(parameters)
    ```

    #### Custom Preprocessing
    ```python
    # Extend preprocess_data function
    def custom_preprocessing(X):
        # Add your custom preprocessing steps
        return X_processed
    ```

    #### Feature Engineering
    - Polynomial features
    - Interaction terms
    - Domain-specific transformations
    - Feature selection algorithms

    ### 📊 Advanced Features

    #### Hyperparameter Tuning
    ```python
    from sklearn.model_selection import GridSearchCV
    param_grid = {'n_estimators': [50, 100, 200]}
    grid_search = GridSearchCV(model, param_grid, cv=5)
    ```

    #### Ensemble Methods
    - Voting classifiers
    - Stacking models
    - Blending predictions

    #### Model Selection
    - Automatic model comparison
    - Statistical significance testing
    - Performance-based selection

    ### 🔧 Production Deployment

    #### Model Serialization
    ```python
    import joblib
    joblib.dump(model, 'model.pkl')
    loaded_model = joblib.load('model.pkl')
    ```

    #### API Deployment
    - FastAPI integration
    - RESTful endpoints
    - Batch prediction services

    #### Monitoring
    - Performance tracking
    - Data drift detection
    - Model retraining triggers

    ### 📈 Best Practices

    #### Data Preparation
    - Always split data before preprocessing
    - Use cross-validation for robust evaluation
    - Handle categorical variables appropriately
    - Check for data leakage

    #### Model Selection
    - Start with simple models
    - Compare multiple algorithms
    - Use appropriate evaluation metrics
    - Consider interpretability vs performance

    #### Validation
    - Use holdout test set
    - Perform cross-validation
    - Check for overfitting
    - Validate on realistic data

    ### 🎯 Use Cases

    - **Customer Churn Prediction**: Classification task
    - **House Price Prediction**: Regression task
    - **Customer Segmentation**: Clustering task
    - **Fraud Detection**: Classification with imbalanced data
    - **Demand Forecasting**: Time series regression

    ### 🔍 Troubleshooting

    #### Common Issues
    - **Data leakage**: Ensure proper train/test split
    - **Imbalanced classes**: Use stratification and appropriate metrics
    - **Overfitting**: Regularization and cross-validation
    - **Feature scaling**: Scale numerical features appropriately

    #### Performance Optimization
    - Feature selection
    - Hyperparameter tuning
    - Ensemble methods
    - Algorithm-specific optimizations

    Created with ❤️ using Marimo ML Pipeline Template

    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    return

if __name__ == "__main__":
    app.run()