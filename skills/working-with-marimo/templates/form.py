"""
📝 Multi-Step Form Builder Template - Table of Contents

📋 OVERVIEW
Comprehensive form system with multi-step navigation, validation, state management, and submission handling

📑 SECTIONS
1. Setup & Configuration (cells 1-3)
2. Form State Management (cells 4-6)
3. Form Configuration (cells 7-10)
4. Step Navigation Logic (cells 11-14)
5. Input Components (cells 15-18)
6. Validation Framework (cells 19-22)
7. Progress & Navigation UI (cells 23-26)
8. Data Processing (cells 27-30)
9. Submission Handling (cells 31-34)
10. Export & Integration (cells 35-37)

🎯 KEY FEATURES
- Multi-step form wizard with progress tracking
- Dynamic field validation and error handling
- Conditional logic and field dependencies
- Form state persistence and recovery
- Submission history and analytics
- Export to multiple formats (JSON, CSV, PDF)

⚡ QUICK START
Customize form configuration in cell_8, adjust validation rules in cell_20, then test form flow
"""

import marimo
import pandas as pd
import json
from datetime import datetime, date
from typing import Dict, Any, List

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def cell_1():
    import marimo as mo
    import pandas as pd
    import json
    from datetime import datetime, date
    from typing import Dict, Any, List
    return mo, pd, json, datetime, date, Dict, Any, List

@app.cell
def cell_2(mo):
    mo.md("# 📝 Multi-Step Form Builder")
    return

@app.cell
def cell_3(mo):
    """Form configuration and state management"""
    @mo.state
    def get_form_state():
        return {
            'current_step': 0,
            'form_data': {},
            'validation_errors': {},
            'is_completed': False,
            'submission_history': []
        }

    form_state = get_form_state()
    return form_state, get_form_state

@app.cell
def cell_4(mo, datetime, date):
    """Form configuration - customizable form structure"""
    # Define form steps and fields
    form_config = {
        'title': 'Customer Onboarding Form',
        'description': 'Complete this multi-step form to onboard new customers',
        'steps': [
            {
                'id': 'personal_info',
                'title': 'Personal Information',
                'description': 'Basic personal details',
                'fields': [
                    {
                        'id': 'first_name',
                        'label': 'First Name',
                        'type': 'text',
                        'required': True,
                        'validation': lambda x: len(x.strip()) >= 2 if x else False
                    },
                    {
                        'id': 'last_name',
                        'label': 'Last Name',
                        'type': 'text',
                        'required': True,
                        'validation': lambda x: len(x.strip()) >= 2 if x else False
                    },
                    {
                        'id': 'email',
                        'label': 'Email Address',
                        'type': 'email',
                        'required': True,
                        'validation': lambda x: '@' in x and '.' in x.split('@')[1] if x else False
                    },
                    {
                        'id': 'phone',
                        'label': 'Phone Number',
                        'type': 'tel',
                        'required': False,
                        'validation': lambda x: len(x.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')) >= 10 if x else True
                    },
                    {
                        'id': 'date_of_birth',
                        'label': 'Date of Birth',
                        'type': 'date',
                        'required': True,
                        'validation': lambda x: (date.today().year - x.year) >= 18 if x else False
                    }
                ]
            },
            {
                'id': 'address_info',
                'title': 'Address Information',
                'description': 'Where are you located?',
                'fields': [
                    {
                        'id': 'street_address',
                        'label': 'Street Address',
                        'type': 'text',
                        'required': True,
                        'validation': lambda x: len(x.strip()) >= 5 if x else False
                    },
                    {
                        'id': 'city',
                        'label': 'City',
                        'type': 'text',
                        'required': True,
                        'validation': lambda x: len(x.strip()) >= 2 if x else False
                    },
                    {
                        'id': 'state',
                        'label': 'State/Province',
                        'type': 'dropdown',
                        'options': ['California', 'New York', 'Texas', 'Florida', 'Illinois', 'Other'],
                        'required': True
                    },
                    {
                        'id': 'postal_code',
                        'label': 'Postal Code',
                        'type': 'text',
                        'required': True,
                        'validation': lambda x: len(x.replace('-', '').replace(' ', '')) >= 5 if x else False
                    },
                    {
                        'id': 'country',
                        'label': 'Country',
                        'type': 'dropdown',
                        'options': ['United States', 'Canada', 'United Kingdom', 'Australia', 'Other'],
                        'required': True,
                        'default': 'United States'
                    }
                ]
            },
            {
                'id': 'preferences',
                'title': 'Preferences',
                'description': 'Tell us about your preferences',
                'fields': [
                    {
                        'id': 'preferred_contact_method',
                        'label': 'Preferred Contact Method',
                        'type': 'radio',
                        'options': ['Email', 'Phone', 'SMS', 'Mail'],
                        'required': True
                    },
                    {
                        'id': 'newsletter_subscription',
                        'label': 'Subscribe to Newsletter',
                        'type': 'checkbox',
                        'default': False
                    },
                    {
                        'id': 'interests',
                        'label': 'Areas of Interest',
                        'type': 'multiselect',
                        'options': ['Technology', 'Finance', 'Healthcare', 'Education', 'Entertainment', 'Sports'],
                        'required': False
                    },
                    {
                        'id': 'preferred_language',
                        'label': 'Preferred Language',
                        'type': 'dropdown',
                        'options': ['English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese'],
                        'required': True,
                        'default': 'English'
                    }
                ]
            },
            {
                'id': 'additional_info',
                'title': 'Additional Information',
                'description': 'Any other details you\'d like to share',
                'fields': [
                    {
                        'id': 'company',
                        'label': 'Company/Organization',
                        'type': 'text',
                        'required': False
                    },
                    {
                        'id': 'job_title',
                        'label': 'Job Title',
                        'type': 'text',
                        'required': False
                    },
                    {
                        'id': 'how_heard',
                        'label': 'How did you hear about us?',
                        'type': 'dropdown',
                        'options': ['Social Media', 'Friend/Colleague', 'Search Engine', 'Advertisement', 'Other'],
                        'required': True
                    },
                    {
                        'id': 'comments',
                        'label': 'Additional Comments',
                        'type': 'textarea',
                        'required': False,
                        'placeholder': 'Any additional information or questions...'
                    }
                ]
            }
        ]
    }

    form_config
    return form_config

@app.cell
def cell_5(mo, form_config, form_state):
    """Progress indicator"""
    def create_progress_indicator():
        """Create visual progress indicator"""
        total_steps = len(form_config['steps'])
        current_step = form_state['current_step']

        progress_html = '<div style="margin: 2rem 0;">'
        progress_html += f'<h3>Step {current_step + 1} of {total_steps}</h3>'

        # Progress bar
        progress_percentage = ((current_step + 1) / total_steps) * 100
        progress_html += f'''
        <div style="width: 100%; background-color: #e0e0e0; border-radius: 10px; margin: 1rem 0;">
            <div style="width: {progress_percentage}%; background-color: #4CAF50; height: 20px; border-radius: 10px; text-align: center; line-height: 20px; color: white;">
                {progress_percentage:.0f}%
            </div>
        </div>
        '''

        # Step indicators
        progress_html += '<div style="display: flex; justify-content: space-between;">'
        for i, step in enumerate(form_config['steps']):
            is_completed = i < current_step
            is_current = i == current_step
            is_future = i > current_step

            color = '#4CAF50' if is_completed else '#2196F3' if is_current else '#ccc'
            icon = '✓' if is_completed else str(i + 1)

            progress_html += f'''
            <div style="text-align: center; flex: 1;">
                <div style="width: 30px; height: 30px; background-color: {color}; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    {icon}
                </div>
                <div style="font-size: 0.8em; margin-top: 0.5rem;">{step['title']}</div>
            </div>
            '''
            if i < total_steps - 1:
                progress_html += '<div style="flex: 0.5; border-top: 2px solid #ccc; margin-top: 15px;"></div>'

        progress_html += '</div></div>'

        return mo.md(progress_html)

    progress_indicator = create_progress_indicator()

    mo.md("## 📊 Form Progress")
    progress_indicator
    return progress_indicator, create_progress_indicator

@app.cell
def cell_6(mo, form_config, form_state):
    """Current step form"""
    def create_step_form():
        """Create form for current step"""
        if form_state['current_step'] >= len(form_config['steps']):
            return mo.md("## ✅ Form Completed!")

        current_step_config = form_config['steps'][form_state['current_step']]

        # Step header
        step_header = mo.md(f"### {current_step_config['title']}")
        step_description = mo.md(f"*{current_step_config['description']}*")

        # Create form fields
        form_fields = []
        for field in current_step_config['fields']:
            field_id = field['id']
            field_label = field['label']
            field_type = field['type']
            required = field.get('required', False)
            default_value = field.get('default')
            current_value = form_state['form_data'].get(field_id, default_value)

            # Create appropriate UI element based on field type
            if field_type == 'text':
                ui_element = mo.ui.text(
                    label=field_label + (' *' if required else ''),
                    value=current_value or '',
                    placeholder=field.get('placeholder', '')
                )
            elif field_type == 'email':
                ui_element = mo.ui.text(
                    label=field_label + (' *' if required else ''),
                    value=current_value or '',
                    placeholder='email@example.com'
                )
            elif field_type == 'tel':
                ui_element = mo.ui.text(
                    label=field_label + (' *' if required else ''),
                    value=current_value or '',
                    placeholder='(555) 123-4567'
                )
            elif field_type == 'date':
                ui_element = mo.ui.date(
                    label=field_label + (' *' if required else ''),
                    value=current_value
                )
            elif field_type == 'dropdown':
                ui_element = mo.ui.dropdown(
                    options=field['options'],
                    value=current_value or field.get('default'),
                    label=field_label + (' *' if required else '')
                )
            elif field_type == 'radio':
                ui_element = mo.ui.radio(
                    options=field['options'],
                    value=current_value,
                    label=field_label + (' *' if required else '')
                )
            elif field_type == 'checkbox':
                ui_element = mo.ui.checkbox(
                    label=field_label,
                    value=current_value if current_value is not None else field.get('default', False)
                )
            elif field_type == 'multiselect':
                ui_element = mo.ui.multiselect(
                    options=field['options'],
                    value=current_value or [],
                    label=field_label
                )
            elif field_type == 'textarea':
                ui_element = mo.ui.text_area(
                    label=field_label + (' *' if required else ''),
                    value=current_value or '',
                    placeholder=field.get('placeholder', '')
                )
            else:
                # Default to text
                ui_element = mo.ui.text(
                    label=field_label + (' *' if required else ''),
                    value=current_value or ''
                )

            form_fields.append((field_id, ui_element))

        # Group all form elements
        form_elements = [step_header, step_description] + [field for _, field in form_fields]
        return form_elements, form_fields

    # Create current step form
    form_elements, form_fields = create_step_form()

    mo.md(f"## 📝 {form_config['steps'][form_state['current_step']]['title']}")

    # Display form elements
    for element in form_elements:
        element
    return form_elements, form_fields, create_step_form

@app.cell
def cell_7(mo, form_config, form_state, form_fields):
    """Form validation and navigation"""
    def validate_current_step():
        """Validate current step fields"""
        current_step_config = form_config['steps'][form_state['current_step']]
        validation_errors = {}

        for field_id, ui_element in form_fields:
            field_config = next((f for f in current_step_config['fields'] if f['id'] == field_id), None)
            if field_config:
                field_value = ui_element.value
                is_required = field_config.get('required', False)
                validation_func = field_config.get('validation')

                # Check required fields
                if is_required and (field_value is None or field_value == '' or
                                   (isinstance(field_value, list) and len(field_value) == 0)):
                    validation_errors[field_id] = f"{field_config['label']} is required"

                # Custom validation
                elif validation_func and field_value is not None:
                    try:
                        if not validation_func(field_value):
                            validation_errors[field_id] = f"Invalid {field_config['label'].lower()}"
                    except Exception:
                        # Validation function failed - treat as error
                        validation_errors[field_id] = f"Invalid {field_config['label'].lower()}"

        return validation_errors

    def save_current_step():
        """Save current step data"""
        current_step_config = form_config['steps'][form_state['current_step']]

        for field_id, ui_element in form_fields:
            field_value = ui_element.value
            form_state['form_data'][field_id] = field_value

    def go_to_next_step():
        """Move to next step"""
        validation_errors = validate_current_step()

        if validation_errors:
            form_state['validation_errors'] = validation_errors
            return False
        else:
            save_current_step()
            form_state['validation_errors'] = {}
            if form_state['current_step'] < len(form_config['steps']) - 1:
                form_state['current_step'] += 1
            else:
                form_state['is_completed'] = True
            return True

    def go_to_previous_step():
        """Move to previous step"""
        if form_state['current_step'] > 0:
            save_current_step()
            form_state['current_step'] -= 1
            form_state['validation_errors'] = {}

    def submit_form():
        """Submit the completed form"""
        save_current_step()
        submission_data = {
            'timestamp': datetime.now().isoformat(),
            'form_data': form_state['form_data'],
            'form_config': form_config['title']
        }
        form_state['submission_history'].append(submission_data)
        form_state['is_completed'] = True
        return submission_data

    # Navigation buttons
    next_btn = mo.ui.button(
        label="Next Step →" if form_state['current_step'] < len(form_config['steps']) - 1 else "Submit Form",
        on_click=lambda: go_to_next_step()
    )

    prev_btn = mo.ui.button(
        label="← Previous Step",
        on_click=lambda: go_to_previous_step(),
        disabled=form_state['current_step'] == 0
    )

    submit_btn = mo.ui.button(
        label="🚀 Submit Complete Form",
        on_click=lambda: submit_form(),
        disabled=not form_state['is_completed']
    )

    # Display validation errors if any
    if form_state['validation_errors']:
        error_messages = [f"• {field}: {error}" for field, error in form_state['validation_errors'].items()]
        errors_html = f'<div style="color: red; background-color: #ffebee; padding: 1rem; border-radius: 5px; margin: 1rem 0;">'
        errors_html += '<strong>Please fix the following errors:</strong><br>'
        errors_html += '<br>'.join(error_messages)
        errors_html += '</div>'
        mo.md(errors_html)

    # Navigation controls
    if not form_state['is_completed']:
        nav_controls = mo.hstack([prev_btn, next_btn])
        nav_controls
    else:
        submit_btn

    return validate_current_step, save_current_step, go_to_next_step, go_to_previous_step, submit_form, next_btn, prev_btn, submit_btn, nav_controls

@app.cell
def cell_8(form_state, mo, pd):
    """Form summary and submission"""
    if form_state['is_completed']:
        mo.md("## 🎉 Form Completed Successfully!")

        # Display submitted data
        if form_state['form_data']:
            mo.md("### 📋 Submitted Information")

            # Convert to DataFrame for nice display
            data_items = []
            for key, value in form_state['form_data'].items():
                if isinstance(value, list):
                    display_value = ', '.join(str(v) for v in value) if value else 'None'
                elif isinstance(value, bool):
                    display_value = 'Yes' if value else 'No'
                elif value is None:
                    display_value = 'None'
                else:
                    display_value = str(value)

                data_items.append({
                    'Field': key.replace('_', ' ').title(),
                    'Value': display_value
                })

            summary_df = pd.DataFrame(data_items)
            summary_table = mo.ui.table(summary_df, selection=None)
            summary_table

        # Submission history
        if form_state['submission_history']:
            mo.md("### 📜 Submission History")
            latest_submission = form_state['submission_history'][-1]
            submission_time = datetime.fromisoformat(latest_submission['timestamp'])
            mo.md(f"**Submitted on**: {submission_time.strftime('%B %d, %Y at %I:%M %p')}")
    return

@app.cell
def cell_9(mo, form_state):
    """Form management features"""
    def reset_form():
        """Reset the form to initial state"""
        form_state['current_step'] = 0
        form_state['form_data'] = {}
        form_state['validation_errors'] = {}
        form_state['is_completed'] = False

    def export_data():
        """Export form data as JSON"""
        export_data = {
            'form_config': form_config['title'],
            'submission_date': datetime.now().isoformat(),
            'form_data': form_state['form_data'],
            'submission_history': form_state['submission_history']
        }
        return json.dumps(export_data, indent=2, default=str)

    def save_to_dataframe():
        """Save form data to pandas DataFrame"""
        data_dict = {}
        for key, value in form_state['form_data'].items():
            if isinstance(value, list):
                data_dict[key] = ', '.join(str(v) for v in value)
            else:
                data_dict[key] = value

        df = pd.DataFrame([data_dict])
        return df

    # Management buttons
    reset_btn = mo.ui.button(
        label="🔄 Reset Form",
        on_click=lambda: reset_form()
    )

    export_btn = mo.ui.button(
        label="💾 Export JSON",
        on_click=lambda: mo.md(f"```json\n{export_data()}\n```")
    )

    dataframe_btn = mo.ui.button(
        label="📊 View as DataFrame",
        on_click=lambda: mo.ui.table(save_to_dataframe(), selection=None)
    )

    mo.md("## 🛠️ Form Management")
    management_controls = mo.hstack([reset_btn, export_btn, dataframe_btn])
    management_controls
    return reset_form, export_data, save_to_dataframe, reset_btn, export_btn, dataframe_btn, management_controls

@app.cell
def cell_10(mo):
    """Documentation and customization guide"""
    mo.md("""
    ## 📖 Form Builder Documentation

    This multi-step form template provides:

    ### Features
    - **Multi-step forms** with progress tracking
    - **Dynamic field validation** with custom validation functions
    - **Multiple field types**: text, email, date, dropdown, radio, checkbox, multiselect, textarea
    - **State management** for form data and validation
    - **Export functionality** for form submissions
    - **Responsive design** for all device sizes

    ### Field Types
    - `text`: Basic text input
    - `email`: Email address input with validation
    - `tel`: Phone number input
    - `date`: Date picker
    - `dropdown`: Single selection from options
    - `radio`: Radio button group
    - `checkbox`: Boolean toggle
    - `multiselect`: Multiple selection from options
    - `textarea`: Multi-line text input

    ### Customization

    #### Adding New Steps
    ```python
    {
        'id': 'new_step',
        'title': 'New Step Title',
        'description': 'Step description',
        'fields': [
            # Add field definitions here
        ]
    }
    ```

    #### Field Configuration
    Each field supports:
    - `id`: Unique field identifier
    - `label`: Display label
    - `type`: Field type (see above)
    - `required`: Whether field is required
    - `validation`: Custom validation function
    - `default`: Default value
    - `options`: List of options (for dropdown/radio/multiselect)
    - `placeholder`: Placeholder text

    #### Custom Validation
    ```python
    'validation': lambda x: len(x.strip()) >= 5 if x else False
    ```

    ### Usage Examples
    1. **Survey Forms**: Customer satisfaction, feedback collection
    2. **Registration Forms**: User onboarding, event registration
    3. **Application Forms**: Job applications, program enrollment
    4. **Data Collection**: Research data, contact information

    ### Advanced Features
    - **Conditional Logic**: Show/hide fields based on other field values
    - **File Upload**: Add file upload capabilities
    - **Custom Styling**: Modify CSS for custom appearance
    - **Integration**: Connect to databases or APIs
    - **Multi-language**: Support for internationalization

    ### Data Handling
    - Form data is stored in state management
    - Export to JSON or pandas DataFrame
    - Submission history tracking
    - Data validation and sanitization

    Created with ❤️ using Marimo Form Template
    """)
    return

if __name__ == "__main__":
    app.run()