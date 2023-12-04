from decouple import config
from jira import JIRA
import pandas as pd
import logging
import itertools
from datetime import datetime
from datetime import date
from functools import cmp_to_key

logging.basicConfig(format="%(asctime)s \t%(message)s", level=logging.INFO)

JIRA_API_TOKEN = config('JIRA_API_TOKEN')

jira_options = {'server': config('JIRA_INSTANCE')}
jira = JIRA(options = jira_options, basic_auth=(config('JIRA_EMAIL'), JIRA_API_TOKEN))
jira_all_fields = jira.fields()
name_map = {field['name']: field['id'] for field in jira_all_fields}

def show_projects():
	projects = jira.projects()
	print(f"Available projects")
	project_index = 0
	for project in projects:
		print(f"{project_index}. {project.name}")
		project_index = project_index + 1
	
	selected_index = input("Select a project number: ")
	selected_index = int(selected_index)
	if selected_index >= 0 and selected_index < len(projects):
		review_tasks(projects[selected_index])

def compare_by_due_date(issue1, issue2):
	due_date1 = issue1.fields.duedate
	due_date2 = issue2.fields.duedate
	today = date.today()
	if due_date1 == None and due_date2 == None:
		return 0
	elif due_date1 != None and due_date2 == None:
		return -1
	elif due_date1 == None and due_date2 != None:
		return 1
	else:
		d1 = datetime.strptime(due_date1, "%Y-%m-%d")
		d2 = datetime.strptime(due_date2, "%Y-%m-%d")
		today = datetime.strptime(str(today), "%Y-%m-%d")
		delta1 = today - d1
		delta2 = today - d2
		if delta1 > delta2:
			return -1
		else:
			return 1

def filter_by_start_date(issue):
	start_date_string = getattr(issue.fields, name_map["Start date"])
	if start_date_string == None:
		return True
	start_date = datetime.strptime(start_date_string, "%Y-%m-%d").date()
	today = date.today()
	return start_date < today

def sort_and_filter_issue(issues):
	sorted_issues = sorted(issues, key=lambda x: x.fields.assignee.displayName)
	grouped_issues_by_assignee = itertools.groupby(sorted_issues, key=lambda x: x.fields.assignee.displayName)
	for assignee, group in grouped_issues_by_assignee:
		print(f"\nAssignee: {assignee}")
		group = sorted(group, key=cmp_to_key(compare_by_due_date))
		group = list(filter(filter_by_start_date, group))
		for issue in group:
			startDate = getattr(issue.fields, name_map["Start date"])
			print(f"Issue: {issue.fields.summary} {issue.fields.updated} {startDate}")
	return grouped_issues_by_assignee

def review_tasks(project):
	issues = jira.search_issues(jql_str=f"project = {project.name}")

	list_all_issues = []
	for singleIssue in issues:
		list_issue = []
		list_issue.append(singleIssue.key)
		list_issue.append(singleIssue.fields.summary)
		list_issue.append(singleIssue.fields.reporter.displayName)
		list_issue.append(singleIssue.fields.assignee)
		list_all_issues.append(list_issue)
		# print('{}: {}:{}'.format(singleIssue.key, singleIssue.fields.summary, 
    #                          singleIssue.fields.reporter.displayName)) 
	df_issues = pd.DataFrame(list_all_issues, columns=["Key", "Summary", "Reporter", "Assignee"])
	column_tiles = ["Key", "Summary", "Reporter", "Assignee"]
	df_issues = df_issues.reindex(columns=column_tiles)
	# logging.info(df_issues)

	# Get assigned issues
	assigned_issues = list(filter(lambda x: x.fields.assignee != None, issues))
	# sorted_issues = sorted(assigned_issues, key=lambda x: x.fields.assignee.displayName)
	# grouped_issues_by_assignee = itertools.groupby(sorted_issues, key=lambda x: x.fields.assignee.displayName)
	# for assignee, group in grouped_issues_by_assignee:
	# 	print(f"\nAssignee: {assignee}")
	# 	for issue in group:
	# 		print(f"Issue: {issue.fields.summary} {issue.fields.updated}")
	
	sort_and_filter_issue(assigned_issues)

	# non_assigned_issues = list(filter(lambda x: x.fields.assignee == None, issues))
	# sorted_issues = sorted(non_assigned_issues, key=lambda x: x.fields.reporter.displayName)
	# grouped_issues_by_reporter = itertools.groupby(sorted_issues, key=lambda x: x.fields.reporter.displayName)
	# for reporter, group in grouped_issues_by_reporter:
	# 	print(f"Reporter: {reporter}")
	# 	for issue in group:
	# 		print(f"Issue: {issue.fields.summary}")


if __name__ == "__main__":
	show_projects()