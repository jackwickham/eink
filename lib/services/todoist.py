import dateutil.parser
import datetime
from lib.resources import Resources
from PIL import Image, ImageDraw
import todoist

class Todoist:
    psuedo_projects = ['Upcoming', 'High Priority']
    upcoming_cutoff = datetime.timedelta(days=3)

    def __init__(self, config, resources: Resources):
        self.config = config
        self.resources = resources
        self.api = todoist.TodoistAPI(config['key'])

    def render(self, image: Image):
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), "Todo List", fill=0, font=self.resources.font_large())

        self.api.sync()

        now = datetime.datetime.now()

        projects = self.psuedo_projects + self.config['projects']

        tasks = {project: [] for project in projects}
        for task in self.api.state['items']:
            if task['checked']:
                continue
            if task['due'] is not None and dateutil.parser.parse(task['due']['date']) < now + self.upcoming_cutoff:
                tasks['Upcoming'].append(task)
            elif task['priority'] > 1:
                tasks['High Priority'].append(task)
            elif task['project_id'] in tasks:
                tasks[task['project_id']].append(task)

        y = 60
        for project_id in projects:
            if len(tasks[project_id]) != 0:
                # Print project name
                name = "Unknown"
                if project_id in self.psuedo_projects:
                    name = project_id
                else:
                    for project in self.api.state['projects']:
                        if project['id'] == project_id:
                            name = project['name']
                            break
                draw.text((10, y), name, fill=0, font=self.resources.font_medium())
                y += 35

                # And all tasks
                for task in tasks[project_id]:
                    draw.text((10, y), '- ' + task['content'], fill=0, font=self.resources.font_small())
                    y += 30
                y += 10
