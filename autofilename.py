import sublime
import sublime_plugin
import os
import ctypes
import platform
import itertools
import string
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
        length = 5 if (self.view.substr(sublime.Region(sel-5,sel-3)) == '\\\\') else 4
        reg = sublime.Region(sel-length,sel-3)
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

    def __init__(self):
        FileNameComplete.isOnFilePathPanel = False

    def on_activated(self,view):
        self.showing_win_drives = False
        FileNameComplete.sep = '/'
        FileNameComplete.is_active = False

    def get_drives(self):
        if 'Windows' not in platform.system():
            return []
        drive_bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        drive_list = list(itertools.compress(string.ascii_uppercase,
            map(lambda x:ord(x) - ord('0'), bin(drive_bitmask)[:1:-1])))
        return [[d+":"+FileNameComplete.sep, d+":"+FileNameComplete.sep] for d in drive_list]

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
        if sel.empty() and ('string.end' in name or 'string.quoted.end.js' in name):
            return True
        if '.css' in name and view.substr(sel.a) == ')':
            return True
        return False

    def on_modified_async(self, view):
        selections = view.sel()

        if len( selections ) > 0:
            sel = selections[0].a
            txt = view.substr(sublime.Region(sel-4,sel-3))

            if (self.showing_win_drives and txt == FileNameComplete.sep):
                self.showing_win_drives = False
                view.run_command('afn_delete_prefixed_slash')

    def on_selection_modified_async(self,view):
        if not view.window():
            return

        # view_name = view.name()
        # buffer_id = view.buffer_id()
        file_name = view.file_name()

        # print( "buffer_id: " + str( buffer_id ) )
        # print( "view_name: " + str( view_name ) )
        # print( "file_name: " + str( file_name ) )
        # print( "FileNameComplete.isOnFilePathPanel:           " + str( FileNameComplete.isOnFilePathPanel ) )
        # print( "FileNameComplete.is_active:                   " + str( FileNameComplete.is_active ) )
        # print( "self.get_setting('afn_use_keybinding', view): " + str( self.get_setting('afn_use_keybinding', view) ) )

        # Do not open autocomplete automatically if keybinding mode is used
        if not FileNameComplete.is_active \
                and self.get_setting('afn_use_keybinding', view) \
                and not FileNameComplete.isOnFilePathPanel:
            return

        # print( "Here on selection_modified_async" )
        selection = view.sel()

        # Fix sublime.py, line 641, in __getitem__ raise IndexError()
        if len( selection ):
            selection = view.sel()[0]
        else:
            return

        # if selection.empty() and self.at_path_end(view):
        if selection.empty():
            scope_contents = view.substr(view.extract_scope(selection.a-1))
            extracted_path = scope_contents.replace('\r\n', '\n').split('\n')[0]

            # print( "scope_contents: " + str( scope_contents ) )

            if('\\' in extracted_path and not '/' in extracted_path):
                FileNameComplete.sep = '\\'

            else:
                FileNameComplete.sep = '/'

            if view.substr(selection.a-1) == FileNameComplete.sep \
                    or len(view.extract_scope(selection.a)) < 3 \
                    or not file_name:
                view.run_command('auto_complete',
                {'disable_auto_insert': True,
                'next_completion_if_showing': False})

        else:
            # print( "FileNameComplete.is_active = False" )
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

        if "string.regexp.js" in view.scope_name(sel):
            return []

        file_name = view.file_name()

        # print( str( valid_scopes ) )
        # print( "file_name: " + str( file_name ) )

        if ( uses_keybinding and file_name ) and not FileNameComplete.is_active:
            return
        if not any(s in view.scope_name(sel) for s in valid_scopes):
            return

        # print( "sel: " + str( sel ) )
        # print( "view: " + str( view ) )
        # print( "blacklist: " + str( blacklist ) )

        if blacklist and any(s in view.scope_name(sel) for s in blacklist):
            return

        cur_path = os.path.expanduser(self.get_cur_path(view, sel))

        # print( "cur_path: " + str( cur_path ) )
        if cur_path.startswith('\\\\') and not cur_path.startswith('\\\\\\') and sublime.platform() == "windows":
            # print( "cur_path.startswith('\\\\')" )
            self.showing_win_drives = True
            return self.get_drives()

        elif cur_path.startswith('/') or cur_path.startswith('\\'):

            if is_proj_rel and file_name:
                proot = self.get_setting('afn_proj_root', view)

                if proot:

                    if not file_name and not os.path.isabs(proot):
                        proot = "/"

                    cur_path = os.path.join(proot, cur_path[1:])

                for f in sublime.active_window().folders():
                    if f in file_name:
                        this_dir = os.path.join(f, cur_path.lstrip('/').lstrip('\\'))

        elif not file_name:
            this_dir = cur_path

        else:
            this_dir = os.path.split(file_name)[0]
            this_dir = os.path.join(this_dir, cur_path)

        # print( "this_dir: " + str( this_dir ) )

        try:
            if os.path.isabs(cur_path) and (not is_proj_rel or not this_dir):
                if sublime.platform() == "windows" and len(view.extract_scope(sel)) < 4:
                    self.showing_win_drives = True
                    return self.get_drives()
                elif sublime.platform() != "windows":
                    this_dir = cur_path

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
            print( "AutoFileName: could not find " + this_dir )
            return
