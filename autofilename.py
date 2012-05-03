import sublime
import sublime_plugin
import os
import glob
from afn_img_utils import get_image_size

class AfnCommitCompCommand(sublime_plugin.TextCommand):
    this_dir = ''

    def insert_dimension(self,edit,dim,name,tag_scope):
        view = self.view
        sel = view.sel()[0].a
        if name in view.substr(tag_scope):
            reg = view.find('(?<='+name+'\=)\s*\"\d{1,5}', tag_scope.a)
            view.replace(edit, reg, '"'+str(dim.get(name)))
        else:
            dimension = str(dim.get(name))
            view.insert(edit, sel+1, ' '+name+'="'+dimension+'"')

    def run(self, edit):
        view = self.view
        sel = view.sel()[0].a
        if not 'string' in view.scope_name(sel): return
        scope = view.extract_scope(sel-1)
        tag_scope = view.extract_scope(scope.a-1)
        region = sublime.Region(sel, scope.b-1)
        view.erase(edit, region)

        path = view.substr(view.extract_scope(sel-1))
        if path.startswith(("'","\"","(")):
            path = path[1:-1]

        path = path[path.rfind('/'):]
        full_path = self.this_dir + path
        if '<img' in view.substr(tag_scope) and path.endswith(('.png','.jpg','.jpeg','.gif')):
            with open(full_path,'rb') as r:
                read_data = r.read()
            dim = get_image_size(read_data)
            self.insert_dimension(edit,dim,'width',tag_scope)
            self.insert_dimension(edit,dim,'height',tag_scope)


class FileNameComplete(sublime_plugin.EventListener):

    committing_filename = False

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "afn_commit-n-trim":
            return self.will_commit(view) == operand

    def scope(self,view,string):
        sel = view.sel()[0].a
        return string in view.scope_name(sel)

    def on_selection_modified(self,view):
        sel = view.sel()[0].a
        v = view
        if self.scope(v,'string.end') or (self.scope(v,'.css') and ')' in view.substr(sel)):
            if view.substr(sel-1) == '/' or len(view.extract_scope(sel)) < 3:
                view.run_command('auto_complete', 
                {'disable_auto_insert': True,
                'next_completion_if_showing': False})

    def will_commit(self, view):
        if self.committing_filename:
            self.committing_filename = False
            return True
        return False

    def fix_dir(self,sdir,fn):
        if fn.endswith(('.png','.jpg','.jpeg','.gif')):
            path = os.path.join(sdir + '/', fn)
            with open(path,'rb') as r:
                read_data = r.read()
            dim = get_image_size(read_data)
            return fn + '\t' + 'w:'+str(dim.get('width'))+" h:"+str(dim.get('height'))
        return fn

    def get_cur_path(self,view,sel):
        scope_contents = view.substr(view.extract_scope(sel-1))
        cur_path = scope_contents.replace('\r\n', '\n').split('\n')[0]
        if cur_path.startswith(("'","\"","(")):
            return cur_path[1:-1]
        return cur_path

    def on_query_completions(self, view, prefix, locations):
        SETTINGS = "autofilename.sublime-settings"
        is_proj_rel = sublime.load_settings(SETTINGS).get("auto_file_name_use_project_root")
        valid_scopes = ["string", "css", "sass", "scss", "less"]
        sel = view.sel()[0].a
        completions = []
        backup = []

        for x in view.find_all("[a-zA-Z]+"):
            backup.append((view.substr(x),view.substr(x)))

        if not any(s in view.scope_name(sel) for s in valid_scopes):
            return []

        cur_path = self.get_cur_path(view, sel)

        if view.extract_scope(sel-1).b - sel > 1:  # if the cursor is not at the end
            wild_pos = sel - view.extract_scope(sel-1).a - 1
            cur_path = cur_path[:wild_pos] + '*' + cur_path[wild_pos:] + '*'

        if is_proj_rel and os.path.isabs(cur_path):
            this_dir = sublime.load_settings(SETTINGS).get("afn_proj_root")
            cur_path = cur_path[1:]
            if len(this_dir) < 2:
                for f in sublime.active_window().folders():
                    if f in view.file_name():
                        this_dir = f
        else:
            if not view.file_name():
                print 'AutoFileName: File not saved.'
                backup.insert(0,('AutoFileName: File Not Saved',''))
                return backup
            this_dir = os.path.split(view.file_name())[0]

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
                if n.startswith('.'): continue
                if not '.' in n: n += '/'
                completions.append((self.fix_dir(this_dir,n), n))
                if completions:
                    self.committing_filename = True
                    AfnCommitCompCommand.this_dir = this_dir
            return completions
        except OSError:
            print "AutoFileName: could not find " + this_dir
            return backup