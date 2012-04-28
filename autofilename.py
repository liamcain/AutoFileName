import sublime
import sublime_plugin
import os
import glob
from afn_img_utils import get_image_size

class AfnCommitCompCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        sel = view.sel()[0].a
        if not 'string' in view.scope_name(sel): return
        scope_end = view.extract_scope(sel-1).b
        region = sublime.Region(sel, scope_end-1)
        view.erase(edit, region)

        path = view.substr(view.extract_scope(sel-1))
        if path.startswith(("'","\"","(")):
            path = path[1:-1]

        if 'img' in view.substr(view.line(sel)) and path.endswith(('.png','.jpg','.jpeg','.gif')):
            with open(path,'r') as r:
                read_data = r.read()
            dim = get_image_size(read_data)
            string = ' width='+str(dim.get('width'))+ ' height='+str(dim.get('height'))
            view.insert(edit, scope_end, string)


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

    def fix_dir(self,dir,fn):
        if not '.' in fn[1:]:
            return fn + '/'
        elif fn.endswith(('.png','.jpg','.jpeg','.gif')):
            path = os.path.join(dir + '/', fn)
            with open(path,'r') as r:
                read_data = r.read()
            dim = get_image_size(read_data)
            return fn + '\t' + 'w:'+str(dim.get('width'))+" h:"+str(dim.get('height'))
        return fn

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
            cur_path = cur_path[:wild_pos] + '*' + cur_path[wild_pos:] + '*'

        if is_proj_rel and os.path.isabs(cur_path):
            this_dir = sublime.load_settings(PACKAGE_SETTINGS).get("afn_proj_root")
            if len(this_dir) < 2:
                for f in sublime.active_window().folders():
                    if f in view.file_name():
                        this_dir = f
                        cur_path = cur_path[1:]
        this_dir = os.path.join(this_dir + '/', cur_path)

        try:
            dir_files = []
            for f in glob.glob(this_dir):
                if os.path.isfile(f):
                    dir_files.append(os.path.basename(f))
                else:
                    dir_files.extend(os.listdir(f))

            for d in list(set(dir_files)):
                n = d.decode('utf-8')
                completions.append((self.fix_dir(this_dir,n), n))
                if completions:
                    self.committing_filename = True
            return completions
        except OSError:
            print "AutoFileName: could not find " + this_dir
            return backup