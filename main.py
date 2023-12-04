from decouple import config
from jira import JIRA
import pandas as pd
import logging
import itertools
from datetime import datetime
from datetime import date
from functools import cmp_to_key
from dateutil import parser

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

JIRA_API_TOKEN = config('JIRA_API_TOKEN')
NO_UPDATE_THRESHOLD = 20

jira_options = {'server': config('JIRA_INSTANCE')}
jira = JIRA(options = jira_options, basic_auth=(config('JIRA_EMAIL'), JIRA_API_TOKEN))
jira_all_fields = jira.fields()
name_map = {field['name']: field['id'] for field in jira_all_fields}

def show_projects():
	projects = jira.projects()
	if len(projects) == 0:
		logging.info("No projects")
		return False
	
	print(f"\nAvailable projects")
	project_index = 0
	for project in projects:
		print(f"\t{project_index}. {project.name}")
		project_index = project_index + 1
	
	print(f"\tq. Exit")
	selected_index = input("Select a project : ")
	if selected_index == 'q':
		return False
	
	try:
		selected_index = int(selected_index)
		if selected_index >= 0 and selected_index < len(projects):
			review_tasks(projects[selected_index])
		else:
			logging.warning("Please select valid project")
	except ValueError:
		logging.error("Please select valid project")
	except:
		logging.error("Something went wrong")
		
	return True

def compare_by_date(date1, date2):
	if date1 == None and date2 == None:
		return 0
	elif date1 != None and date2 == None:
		return -1
	elif date1 == None and date2 != None:
		return 1
	else:
		d1 = datetime.strptime(date1, "%Y-%m-%d")
		d2 = datetime.strptime(date2, "%Y-%m-%d")
		today = date.today()
		today = datetime.strptime(str(today), "%Y-%m-%d")
		delta1 = today - d1
		delta2 = today - d2
		if delta1 > delta2:
			return -1
		else:
			return 1

def compare_by_start_date(issue1, issue2):
	start_date1 = getattr(issue1.fields, name_map["Start date"])
	start_date2 = getattr(issue2.fields, name_map["Start date"])
	return compare_by_date(start_date1, start_date2)

def compare_by_due_date(issue1, issue2):
	due_date1 = issue1.fields.duedate
	due_date2 = issue2.fields.duedate
	if due_date1 == due_date2:
		return compare_by_start_date(issue1, issue2)
	return compare_by_date(due_date1, due_date2)

def filter_by_update_date(issue):
	updated_date = issue.fields.updated
	if updated_date == None:
		return False

	# updated_time = datetime.strptime(updated_date, "%Y-%m-%dT%H:%M:%S.%f%z")
	updated_time = parser.isoparse(updated_date)
	updated_time = updated_time.astimezone().replace(tzinfo=None)
	now = datetime.now()
	diff = (now - updated_time).total_seconds() / 60
	return diff > NO_UPDATE_THRESHOLD

def filter_by_status(issue):
	return issue.fields.status != None and issue.fields.status.name != "Done"

def sort_by_status(issue):
	if issue.fields.status.name == "In Progress":
		return 0
	else:
		return 1

def sort_and_filter_issue(issues):
	issues = sorted(issues, key=cmp_to_key(compare_by_due_date))
	issues = list(filter(filter_by_update_date, issues))
	issues = list(filter(filter_by_status, issues))
	issues = sorted(issues, key=sort_by_status)
	return issues

def print_issues(issues):
	list_all_issues = []
	for issue in issues:
		startDate = getattr(issue.fields, name_map["Start date"])
		list_issue = []
		list_issue.append(issue.key)
		list_issue.append(issue.fields.summary)
		list_issue.append(issue.fields.reporter.displayName)
		list_issue.append(issue.fields.assignee)
		list_issue.append(issue.fields.duedate)
		list_issue.append(issue.fields.updated)
		list_issue.append(startDate)
		list_issue.append(issue.fields.status)
		list_all_issues.append(list_issue)

	df_issues = pd.DataFrame(list_all_issues, columns=["Key", "Summary", "Reporter", "Assignee", "Due Date", "Updated", "Start Date", "Status"])
	df_issues.style.set_properties(**{'text-align': 'left'})
	column_tiles = ["Key", "Summary", "Due Date", "Updated", "Start Date", "Status"]
	df_issues = df_issues.reindex(columns=column_tiles)
	print(df_issues)

def request_update_from_assignee(PersonName, TaskData):
	logging.info(f"request_update_from_assignee : {PersonName} - {TaskData}")

def request_update_from_reporter(PersonName, TaskData):
	logging.info(f"request_update_from_reporter : {PersonName} - {TaskData}")

def review_tasks(project):
	issues = jira.search_issues(jql_str=f"project = {project.name}")

	if len(issues) == 0:
		logging.info("No issues")
		return

	# Get assigned issues
	assigned_issues = list(filter(lambda x: x.fields.assignee != None, issues))
	if len(assigned_issues) > 0:
		sorted_issues = sorted(assigned_issues, key=lambda x: x.fields.assignee.displayName)
		grouped_issues_by_assignee = itertools.groupby(sorted_issues, key=lambda x: x.fields.assignee.displayName)
		for assignee, group in grouped_issues_by_assignee:
			# print(f"\nAssignee: {assignee}")
			group = sort_and_filter_issue(group)
			if len(group) > 0:
				request_update_from_assignee(assignee, group[0])
			# print_issues(group)
	else:
		logging.info("No assigned issues")
		

	non_assigned_issues = list(filter(lambda x: x.fields.assignee == None, issues))
	if len(non_assigned_issues) > 0:
		sorted_issues = sorted(non_assigned_issues, key=lambda x: x.fields.reporter.displayName)
		grouped_issues_by_reporter = itertools.groupby(sorted_issues, key=lambda x: x.fields.reporter.displayName)
		for reporter, group in grouped_issues_by_reporter:
			# print(f"\nReporter: {reporter}")
			group = sort_and_filter_issue(group)
			if len(group) > 0:
				request_update_from_reporter(reporter, group[0])
			# print_issues(group)
	else:
		logging.info("No unassigned issues")

def main():
	while True:
		if show_projects():
			continue
		else:
			break
if __name__ == "__main__":
	main()
