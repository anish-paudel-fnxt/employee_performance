from flask import Flask, render_template, request, abort
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from sklearn.metrics import precision_score, recall_score, f1_score

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

class UploadForm(FlaskForm):
    file = FileField('Upload Excel File', validators=[DataRequired()])
    submit = SubmitField('Upload')

def calculate_performance_score(row):
    try:
        weights = {
            'No_of_years_experience': 0.10,
            'KPIs_meet >80': 0.2,
            'Previous_Year_Rating': 0.10,
            'Soft_Skills': 0.2,
            'Supervisor_Review': 0.2,
            'Job_Satisfaction': 0.2
        }
        weighted_sum = sum(row[feature] * weight for feature, weight in weights.items() if pd.notnull(row[feature]))
        return weighted_sum
    except Exception as e:
        return 0

# Function to calculate precision, recall, and F1 score for KPIs_meet >80 column
def calculate_kpi_metrics(df):
    y_true = df['KPIs_meet >80'].astype(int)
    y_pred = (df['Performance_score'] > df['Performance_score'].mean()).astype(int)

    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    return precision, recall, f1

def filter_above_average(df):
    # Convert 'Y' and 'N' in KPIs_meet >80 to 1 and 0
    df['KPIs_meet >80'] = df['KPIs_meet >80'].replace({'Y': 1, 'N': 0})

    # Replace null values in No_of_years_experience with 0
    df['No_of_years_experience'].fillna(0, inplace=True)

    # Calculate performance score for all candidates
    df['Performance_score'] = df.apply(calculate_performance_score, axis=1)
    
    # Calculate average performance score
    average_score = df['Performance_score'].mean()

    # Find candidates with performance score above average
    above_average_performance = df[df['Performance_score'] > average_score]

    # Calculate total counts of male and female candidates
    male_count = df[df['gender'] == 'M'].shape[0]
    female_count = df[df['gender'] == 'F'].shape[0]

    # Find candidate IDs performing above performance score
    above_average_ids = above_average_performance['Employee_ID'].tolist()

    # Find total count of employees above average performance score
    total_above_average = above_average_performance.shape[0]

    # Find candidate with max performance score
    max_score_candidate = above_average_performance.sort_values(by='Performance_score', ascending=False).head(1)

    # Generate department performance chart
    department_performance = above_average_performance.groupby('Department').size()

    return (above_average_performance, average_score, above_average_ids, 
            male_count, female_count, total_above_average, max_score_candidate, 
            department_performance)

# Function to calculate highest performing employee
def calculate_highest_performer(df):
    if df.empty:
        return None, None
    
    max_score_row = df.loc[df['Performance_score'].idxmax()]
    return max_score_row['Employee_ID'], max_score_row['Department']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        excel_file = form.file.data
        if excel_file:
            try:
                # Read the Excel file
                df = pd.read_excel(excel_file)

                # Filter and process data
                try:
                    (above_average_performance, 
                    average_score, 
                    above_average_ids, 
                    male_count, 
                    female_count, 
                    total_above_average, 
                    max_score_candidate, 
                    department_performance) = filter_above_average(df)
                    
                    # Calculate highest performing employee ID and department
                    highest_employee_id, highest_department = calculate_highest_performer(above_average_performance)
                except ValueError:
                    male_count = df[df['gender'] == 'M'].shape[0]
                    female_count = df[df['gender'] == 'F'].shape[0]
                    total_above_average = 0
                    max_score_candidate = None
                    department_performance = None
                    highest_employee_id = None
                    highest_department = None

                # Calculating KPIs score based on department
                kpis_department = df.groupby('Department')['KPIs_meet >80'].sum()

                # Creating pie chart for KPIs score based on department
                pie_img = io.BytesIO()
                plt.figure(figsize=(6, 6))
                kpis_department.plot(kind='pie', autopct='%1.1f%%', colors=plt.cm.tab10.colors)
                plt.title('KPIs Meet >80% by Department')
                plt.axis('equal')
                plt.savefig(pie_img, format='png')
                pie_img.seek(0)
                pie_url = base64.b64encode(pie_img.getvalue()).decode()

                # Bar chart to visualize male and female counts
                bar_chart_img = io.BytesIO()
                plt.figure(figsize=(6, 6))
                plt.bar(['M', 'F'], [male_count, female_count], color=['blue', 'pink'])
                plt.title('Male and Female Candidates')
                plt.xlabel('Gender')
                plt.ylabel('Count')
                plt.savefig(bar_chart_img, format='png')
                bar_chart_img.seek(0)
                bar_chart_url = base64.b64encode(bar_chart_img.getvalue()).decode()

                # Department Performance Chart
                department_chart_img = io.BytesIO()
                plt.figure(figsize=(6, 6))
                department_performance.plot(kind='bar')
                plt.title('Department Performance')
                plt.xlabel('Department')
                plt.ylabel('Count')
                plt.tight_layout()
                plt.savefig(department_chart_img, format='png')
                department_chart_img.seek(0)
                department_chart_encoded = base64.b64encode(department_chart_img.getvalue()).decode()

                # Calculate precision, recall, and F1 score for KPIs_meet >80 column
                precision, recall, f1 = calculate_kpi_metrics(above_average_performance)

                return render_template('result.html', 
                                       tables=[df.to_html(classes='data')],
                                       titles=df.columns.values,
                                       male_count=male_count,
                                       female_count=female_count,
                                       pie_chart=pie_url,
                                       bar_chart=bar_chart_url,
                                       average_score=average_score,
                                       above_average_ids=above_average_ids,
                                       total_above_average=total_above_average,
                                       max_score_candidate=max_score_candidate,
                                       department_chart=department_chart_encoded,
                                       highest_performing_employee_id=highest_employee_id,
                                       highest_performing_department=highest_department,
                                       precision=precision,
                                       recall=recall,
                                       f1=f1
                                      )



            except Exception as e:
                error_message = f




            except Exception as e:
                error_message = f"An error occurred while processing the file: {str(e)}"
                return render_template('error.html', error=error_message)
    return render_template('upload.html', form=form)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
