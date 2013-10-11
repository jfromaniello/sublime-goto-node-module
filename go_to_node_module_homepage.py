import sublime_plugin
import os
from subprocess import Popen, PIPE
from tempfile import SpooledTemporaryFile as tempfile
import json
import sys

class GoToNodeModuleHomepage(sublime_plugin.TextCommand):

    def open_url(self, resolvers, edit):
        def do_open (index):
            url = resolvers[index]()
            if sys.platform=='win32':
                Popen(['start', url], shell= True)

            elif sys.platform=='darwin':
                print 'open ' + url
                Popen(['open', url])

            else:
                try:
                    Popen(['xdg-open', url])
                except OSError:
                    print "Can't find xdg-open"
                    # er, think of something else to try
                    # xdg-open *should* be supported by recent Gnome, KDE, Xfce

        return do_open

    def get_suggestion_from_nodemodules(self):
        resolvers = []
        suggestions = []
        current_file_dirs = self.view.file_name().split(os.path.sep)
        current_dir = os.path.split(self.view.file_name())[0]

        def get_url(dir):
            json_data =  open(os.path.join(dir, 'package.json')).read()
            print 'package json data:'
            print json_data
            package_json = json.loads( json_data )
            if 'homepage' in package_json:
                return package_json['homepage']
            else:
                if 'repository' in package_json:
                    repo = package_json['repository']['url'] if 'url' in package_json['repository'] else package_json['repository']
                    repo = repo.replace('git://', 'http://')
                    return repo

        for x in range(len(self.view.window().folders()[0].split(os.path.sep)), len(current_file_dirs))[::-1]:
            candidate = os.path.join(current_dir, "node_modules")
            if os.path.exists(candidate):
                for dir in [name for name in os.listdir(candidate)
                                 if os.path.isdir(os.path.join(candidate, name)) and name != ".bin"]:
                    resolvers.append(lambda dir=dir: get_url(os.path.join(candidate, dir)))
                    suggestions.append("module: " + dir)
                break
            current_dir = os.path.split(current_dir)[0]
        return [resolvers, suggestions]

    def get_suggestion_native_modules(self):
        try:
            f = tempfile()
            f.write('console.log(Object.keys(process.binding("natives")))')
            f.seek(0)
            jsresult = (Popen(['node'], stdout=PIPE, stdin=f, shell=True)).stdout.read().replace("'", '"')
            f.close()

            results = json.loads(jsresult)

            result = [[(lambda ni=ni: "http://nodejs.org/api/%s.html" % ni) for ni in results],
                    ["native: " + ni for ni in results]]
            return result
        except Exception:
            return [[], []]



    def run(self, edit):
        suggestions = []
        resolvers = []

        #create suggestions for modules in node_module folder
        [resolvers_from_nm, suggestions_from_nm] = self.get_suggestion_from_nodemodules()
        resolvers += resolvers_from_nm
        suggestions += suggestions_from_nm

        #create suggestions from native modules
        [resolvers_from_native, suggestions_from_nm] = self.get_suggestion_native_modules()
        resolvers += resolvers_from_native
        suggestions += suggestions_from_nm

        self.view.window().show_quick_panel(suggestions, self.open_url(resolvers, edit))
