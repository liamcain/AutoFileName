import sublime
import sublime_plugin
import os
import glob

class AfnCommitCompCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()[0].a
        scope_end = view.extract_scope(sel-1).b - 1
        region = sublime.Region(sel, scope_end)
        view.erase(edit, region)

        view.insert(edit, sel+3, 'height=""')

class FileNameComplete(sublime_plugin.EventListener):

    committing_filename = False

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "afn_commit-n-trim":
            return self.will_commit(view) == operand

    def will_commit(self, view):
        if self.committing_filename:
            self.committing_filename = False
            return True
        return False

    def prev_has(self, view, string):
        sel = view.sel()[0].a
        return string in view.substr(sublime.Region(sel-1, sel))

    def is_empty_string(self,view,sel):
        string = view.substr(view.extract_scope(sel))
        return len(string) < 3

    def fix_dir(self, path):
        if not '.' in path:
            return path + '/'
        return path

    def on_query_completions(self, view, prefix, locations):
        completions = []
        valid_scopes = ["string", "css", "sass", "scss", "less"]
        PACKAGE_SETTINGS = "autofilename.sublime-settings"
        is_proj_rel = sublime.load_settings(PACKAGE_SETTINGS).get("auto_file_name_use_project_root")
        backup = []
        sel = view.sel()[0].a

        for x in view.find_all("[a-zA-Z]+"):
                    backup.append(view.substr(x))

        if not any(s in view.scope_name(sel) for s in valid_scopes):
            return backup

        this_dir = os.path.split(view.file_name())[0] + os.path.sep
        cur_path = view.substr(view.extract_scope(sel-1)).replace('\r\n', '\n').split('\n')[0]
        if cur_path.startswith(("'","\"","(")):
            cur_path = cur_path[1:-1]

        if view.extract_scope(sel-1).b - sel != 1:
            wild_pos = sel - view.extract_scope(sel-1).a - 1
            cur_path = cur_path[:wild_pos] + '*' + cur_path[wild_pos:]
        cur_path += '*'

        if is_proj_rel and os.path.isabs(cur_path):
            this_dir = sublime.load_settings(PACKAGE_SETTINGS).get("afn_proj_root")
            if len(this_dir) < 2:
                for f in sublime.active_window().folders():
                    if f in view.file_name():
                        this_dir = f
        else:
            this_dir = os.path.join(this_dir, cur_path)

        try:
            dir_files = []
            for f in glob.glob(this_dir):
                if os.path.isfile(f): 
                    dir_files.append(os.path.basename(f))
                else:
                    dir_files.extend(os.listdir(f))

            for d in list(set(dir_files)):
                n = d.decode('utf-8')
                completions.append((self.fix_dir(n), n))
                if completions:
                    self.committing_filename = True
            return completions
        except OSError:
            print "AutoFileName: could not find " + this_dir
            return backup