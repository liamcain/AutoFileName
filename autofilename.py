import sublime
import sublime_plugin
import os
from .getimageinfo import getImageInfo

class AfnShowFilenames(sublime_plugin.TextCommand):
    def run(self, edit):
        FileNameComplete.is_active = True
        self.view.run_command('auto_complete',
                {'disable_auto_insert': True,
                'next_completion_if_showing': False})

class AfnSettingsPanel(sublime_plugin.WindowCommand):
    def run(self):
        use_pr = '✗ Stop using project root' if self.get_setting('afn_use_project_root') else '✓ Use Project Root'
        use_dim = '✗ Disable HTML Image Dimension insertion' if self.get_setting('afn_insert_dimensions') else '✓ Auto-insert Image Dimensions in HTML'
        p_root = self.get_setting('afn_proj_root')

        menu = [
                [use_pr, p_root],
                [use_dim, '<img src="_path_" width = "x" height = "y" >']
               ]
        self.window.show_quick_panel(menu, self.on_done)

    def on_done(self, value):
        settings = sublime.load_settings('autofilename.sublime-settings')
        if value == 0:
            use_pr = settings.get('afn_use_project_root')
            settings.set('afn_use_project_root', not use_pr)
        if value == 1:
            use_dim = settings.get('afn_use_project_root')
            settings.set('afn_use_project_root', not use_dim)

    def get_setting(self,string,view=None):
        if view and view.settings().get(string):
            return view.settings().get(string)
        else:
            return sublime.load_settings('autofilename.sublime-settings').get(string)

# Used to remove the / or \ when autocompleting a Windows drive (eg. /C:/path)
class AfnDeletePrefixedSlash(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()[0].a
        reg = sublime.Region(sel-4,sel-3)
        self.view.erase(edit, reg)

# inserts width and height dimensions into img tags. HTML only
class InsertDimensionsCommand(sublime_plugin.TextCommand):
    this_dir = ''

    def insert_dimension(self,edit,dim,name,tag_scope):
        view = self.view
        sel = view.sel()[0].a

        if name in view.substr(tag_scope):
            reg = view.find('(?<='+name+'\=)\s*\"\d{1,5}', tag_scope.a)
            view.replace(edit, reg, '"'+str(dim))
        else:
            dimension = str(dim)
            view.insert(edit, sel+1, ' '+name+'="'+dimension+'"')

    def get_setting(self,string,view=None):
        if view and view.settings().get(string):
            return view.settings().get(string)
        else:
            return sublime.load_settings('autofilename.sublime-settings').get(string)


    def insert_dimensions(self, edit, scope, w, h):
        view = self.view

        if self.get_setting('afn_insert_width_first',view):
            self.insert_dimension(edit,h,'height', scope)
            self.insert_dimension(edit,w,'width', scope)
        else:
            self.insert_dimension(edit,w,'width', scope)
            self.insert_dimension(edit,h,'height', scope)


    # determines if there is a template tag in a given region.  supports HTML and template languages.
    def img_tag_in_region(self, region):
        view = self.view

        # handle template languages but template languages like slim may also contain HTML so
        # we do a check for that as well
        return view.substr(region).strip().startswith('img') | ('<img' in view.substr(region))


    def run(self, edit):
        view = self.view
        view.run_command("commit_completion")
        sel = view.sel()[0].a

        if not 'html' in view.scope_name(sel): return
        scope = view.extract_scope(sel-1)

        # if using a template language, the scope is set to the current line
        tag_scope = view.line(sel) if self.get_setting('afn_template_languages',view) else view.extract_scope(scope.a-1)

        path = view.substr(scope)
        if path.startswith(("'","\"","(")):
            path = path[1:-1]

        path = path[path.rfind(FileNameComplete.sep):] if FileNameComplete.sep in path else path
        full_path = self.this_dir + path

        if self.img_tag_in_region(tag_scope) and path.endswith(('.png','.jpg','.jpeg','.gif')):
            with open(full_path,'rb') as r:
                read_data = r.read() if path.endswith(('.jpg','.jpeg')) else r.read(24)
            w, h = getImageInfo(read_data)

            self.insert_dimensions(edit, tag_scope, w, h)


# When backspacing through a path, selects the previous path component
class ReloadAutoCompleteCommand(sublime_plugin.TextCommand):
    def run(self,edit):
        view = self.view
        view.run_command('hide_auto_complete')
        view.run_command('left_delete')
        sel = view.sel()[0].a

        scope = view.extract_scope(sel-1)
        scope_text = view.substr(scope)
        slash_pos = scope_text[:sel - scope.a].rfind(FileNameComplete.sep)
        slash_pos += 1 if slash_pos < 0 else 0

        region = sublime.Region(scope.a+slash_pos+1,sel)
        view.sel().add(region)


class FileNameComplete(sublime_plugin.EventListener):
    def on_activated(self,view):
        self.showing_win_drives = False
        FileNameComplete.is_active = False
        FileNameComplete.sep = '/'

    def get_drives(self):
    # Search through valid drive names and see if they exist. (stolen from Facelessuser)
        return [[d+":"+FileNameComplete.sep, d+":"+FileNameComplete.sep] for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(d + ":")]

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "afn_insert_dimensions":
            return self.get_setting('afn_insert_dimensions',view) == operand
        if key == "afn_deleting_slash":  # for reloading autocomplete
            sel = view.sel()[0]
            valid = self.at_path_end(view) and sel.empty() and view.substr(sel.a-1) == FileNameComplete.sep
            return valid == operand
        if key == "afn_use_keybinding":
            return self.get_setting('afn_use_keybinding',view) == operand

    def at_path_end(self,view):
        sel = view.sel()[0]
        name = view.scope_name(sel.a)
        if sel.empty() and 'string.end' in name:
            return True
        if '.css' in name and view.substr(sel.a) == ')':
            return True
        return False

    def on_modified(self, view):
        sel = view.sel()[0].a
        txt = view.substr(sublime.Region(sel-4,sel-3))
        if (self.showing_win_drives and txt == FileNameComplete.sep):
            self.showing_win_drives = False
            view.run_command('afn_delete_prefixed_slash')

    def on_selection_modified_async(self,view):
        if not view.window():
            return
        sel = view.sel()[0]
        if sel.empty() and self.at_path_end(view):
            scope_contents = view.substr(view.extract_scope(sel.a-1))
            p = scope_contents.replace('\r\n', '\n').split('\n')[0]
            if('\\' in p and not '/' in p):
                FileNameComplete.sep = '\\'
            else:
                FileNameComplete.sep = '/'
            if view.substr(sel.a-1) == FileNameComplete.sep or len(view.extract_scope(sel.a)) < 3:
                view.run_command('auto_complete',
                {'disable_auto_insert': True,
                'next_completion_if_showing': False})
        else:
            FileNameComplete.is_active = False

    def fix_dir(self,sdir,fn):
        if fn.endswith(('.png','.jpg','.jpeg','.gif')):
            path = os.path.join(sdir, fn)
            with open(path,'rb') as r:
                read_data = r.read() if path.endswith(('.jpg','.jpeg')) else r.read(24)
            w, h = getImageInfo(read_data)
            return fn+'\t'+'w:'+ str(w) +" h:" + str(h)
        return fn

    def get_cur_path(self,view,sel):
        scope_contents = view.substr(view.extract_scope(sel-1)).strip()
        cur_path = scope_contents.replace('\r\n', '\n').split('\n')[0]
        if cur_path.startswith(("'","\"","(")):
            cur_path = cur_path[1:-1]

        return cur_path[:cur_path.rfind(FileNameComplete.sep)+1] if FileNameComplete.sep in cur_path else ''

    def get_setting(self,string,view=None):
        if view and view.settings().get(string):
            return view.settings().get(string)
        else:
            return sublime.load_settings('autofilename.sublime-settings').get(string)

    def on_query_completions(self, view, prefix, locations):
        is_proj_rel = self.get_setting('afn_use_project_root',view)
        valid_scopes = self.get_setting('afn_valid_scopes',view)
        blacklist = self.get_setting('afn_blacklist_scopes', view)
        uses_keybinding = self.get_setting('afn_use_keybinding', view)

        sel = view.sel()[0].a
        this_dir = ""
        completions = []

        if uses_keybinding and not FileNameComplete.is_active:
            return
        if not any(s in view.scope_name(sel) for s in valid_scopes):
            return
        if any(s in view.scope_name(sel) for s in blacklist):
            return

        cur_path = os.path.expanduser(self.get_cur_path(view, sel))


        if cur_path.startswith('/') or cur_path.startswith('\\'):
            if is_proj_rel:
                proot = self.get_setting('afn_proj_root', view)
                if proot:
                    if not view.file_name() and not os.path.isabs(proot):
                        proot = "/"
                    cur_path = os.path.join(proot, cur_path[1:])
                else:
                    for f in sublime.active_window().folders():
                        if f in view.file_name():
                            cur_path = f
        elif not view.file_name():
            return
        else:
            this_dir = os.path.split(view.file_name())[0]
        this_dir = os.path.join(this_dir, cur_path)

        try:
            if sublime.platform() == "windows" and len(view.extract_scope(sel)) < 4 and os.path.isabs(cur_path):
                self.showing_win_drives = True
                return self.get_drives()
            self.showing_win_drives = False
            dir_files = os.listdir(this_dir)

            for d in dir_files:
                if d.startswith('.'): continue
                if not '.' in d: d += FileNameComplete.sep
                completions.append((self.fix_dir(this_dir,d), d))
            if completions:
                InsertDimensionsCommand.this_dir = this_dir
                return completions
            return
        except OSError:
            print("AutoFileName: could not find " + this_dir)
            return
