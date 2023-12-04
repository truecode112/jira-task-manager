from decouple import config
from jira import JIRA
import pandas as pd

JIRA_API_TOKEN = config('JIRA_API_TOKEN')

jira_options = {'server': config('JIRA_INSTANCE')}
jira = JIRA(options = jira_options, basic_auth=(config('JIRA_EMAIL'), JIRA_API_TOKEN))

def show_projects():
	projects = jira.projects()
	print("Available projects")
	project_index = 0
	for project in projects:
		print(f"{project_index}. {project.name}")
		project_index = project_index + 1
	
	selected_index = input("Select a project number: ")
	selected_index = int(selected_index)
	if selected_index >= 0 and selected_index < len(projects):
		review_tasks(projects[selected_index])

def review_tasks(project):
	issues = jira.search_issues(jql_str=f"project = {project.name}")

	list_all_issues = []
	for singleIssue in issues:
		list_issue = []
		list_issue.append(singleIssue.key)
		list_issue.append(singleIssue.fields.summary)
		list_issue.append(singleIssue.fields.reporter.displayName)
		list_all_issues.append(list_issue)
		# print('{}: {}:{}'.format(singleIssue.key, singleIssue.fields.summary, 
    #                          singleIssue.fields.reporter.displayName)) 
	df_issues = pd.DataFrame(list_all_issues, columns=["Key", "Summary", "Reporter"])
	column_tiles = ["Key", "Summary", "Reporter"]
	df_issues = df_issues.reindex(columns=column_tiles)
	print(df_issues)

if __name__ == "__main__":
	show_projects()