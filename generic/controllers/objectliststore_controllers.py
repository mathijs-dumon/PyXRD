# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import gtk
 
from generic.views.treeview_tools import new_text_column, setup_treeview
from base_controllers import DialogController, BaseController

class ObjectTreeviewMixin():
    """
        Mixin that provides some generic methods to acces or set the objects selected in a treeview.
    """
    
    def get_selected_object(self, tv):
        objects = ObjectTreeviewMixin.get_selected_objects(self, tv)
        if objects is not None and len(objects) == 1:
            return objects[0]
        return None
        
    def get_selected_objects(self, tv):
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:      
            model, paths = selection.get_selected_rows()
            return map(model.get_user_data_from_path, paths)
        return None
        
    def get_selected_paths(self, tv):
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:      
            model, paths = selection.get_selected_rows()
            return paths
        return None
        
    def get_all_objects(self, tv):
        return tv.get_model().get_raw_model_data()
        
    def set_selected_paths(self, tv, paths):
        selection = tv.get_selection()
        selection.unselect_all()
        for path in paths:
            selection.select_path(path)

class ObjectListStoreMixin(ObjectTreeviewMixin):
    """
        Mixin that can be used for regular ObjectListStoreControllers (two-pane view).
    """
    
    model_property_name = ""
    multi_selection = True
    edit_controller = None
    edit_view = None
    columns = [ ("Object name", 0) ]
    delete_msg = "Deleting objects is irreverisble!\nAre You sure you want to continue?"

    def __init__(self, model_property_name="", multi_selection=None, columns=[], delete_msg=""):
        self.model_property_name = model_property_name or self.model_property_name
        self.multi_selection = multi_selection or self.multi_selection
        
        self.liststore.connect("item-removed", self.on_item_removed)
        self.liststore.connect("item-inserted", self.on_item_inserted)
        
        self.columns = columns or self.columns
        self.delete_msg = delete_msg or self.delete_msg

    @property
    def liststore(self):
        if self.model!=None:
            return getattr(self.model, self.model_property_name)
        else:
            return None

    def get_new_edit_view(self, obj):
        if obj == None:
            return self.view.none_view
        else:
            raise NotImplementedError, ("Unsupported object type; subclasses of"
                " ObjectListStoreMixin need to override get_new_edit_view for"
                " objects not equalling None!")
        
    def get_new_edit_controller(self, obj, view, parent=None):
        if obj == None:
            return None
        else:
            raise NotImplementedError, ("Unsupported object type; subclasses of"
                " ObjectListStoreMixin need to override get_new_edit_controller"
                " for objects not equalling None!")
    
    def edit_object(self, obj):
        self.edit_view = self.get_new_edit_view(obj)
        self.edit_controller =  self.get_new_edit_controller(obj, self.view.set_edit_view(self.edit_view), parent=self.parent)
        return True

    def register_adapters(self):
        if self.model is not None:
            # connects the treeview to the liststore
            tv = self.view.treeview
            self.setup_treeview(tv)
            
            self.set_object_sensitivities(False)
        # we can now edit 'nothing':
        self.edit_object(None)

    def setup_treeview(self, tv):
        """
            Sets up the treeview with columns based on the columns-tuple passed
            to the __init__ or set in the class definition.
            Subclasses can override either this method completely or provide
            custom column creation code on a per-column basis.
            To do this, create a method for e.g. column with colnr = 2:
            def setup_treeview_col_2(self, treeview, name, col_descr, col_index, tv_col_nr):
                ...
            If a string description of the column number was given, e.g. for the
            column c_name the definition should be:
            def setup_treeview_col_c_name(self, treeview, name, col_descr, col_index, tv_col_nr):
                ...
                
            The method should return True upon succes or False otherwise.
        """
        sel_mode = gtk.SELECTION_MULTIPLE if self.multi_selection else gtk.SELECTION_SINGLE
        setup_treeview(
            tv, self.liststore, 
            sel_mode=sel_mode,
            on_selection_changed=self.objects_tv_selection_changed)
        
        #reset:
        for col in tv.get_columns():
            tv.remove_column(col)
        
        #add columns
        for tv_col_nr, (name, col_descr) in enumerate(self.columns):
            try:
                col_index = int(colnr)
            except:
                col_index = getattr(self.liststore, str(col_descr), col_descr)
                
            handled = False                
            if hasattr(self, "setup_treeview_col_%s" % str(col_descr)):
                handler = getattr(self, "setup_treeview_col_%s" % str(col_descr))
                if callable(handler):
                    handled = handler(tv, name, col_descr, col_index, tv_col_nr)
            # custom handler failed or not present, default text column:
            if not handled:
                tv.append_column(new_text_column(
                    name, text_col=col_index,
                    resizable=(tv_col_nr==0),
                    expand=(tv_col_nr==0),
                    xalign=0.0 if tv_col_nr == 0 else 0.5))

    def set_object_sensitivities(self, value):
        if self.view.edit_view != None:
            self.view.edit_view.get_top_widget().set_sensitive(value)
        self.view["button_del_object"].set_sensitive(value)
        self.view["button_save_object"].set_sensitive(value)

    def get_selected_object(self):
        return ObjectTreeviewMixin.get_selected_object(self, self.view.treeview)
        
    def get_selected_objects(self):
        return ObjectTreeviewMixin.get_selected_objects(self, self.view.treeview)

    def get_all_objects(self):
        return ObjectTreeviewMixin.get_all_objects(self, self.view.treeview)

    def select_object(self, obj, unselect_all=True):
        selection = self.view.treeview.get_selection()
        if unselect_all: selection.unselect_all()
        if obj:
            path = self.liststore.on_get_path(obj)
            if path!=None: selection.select_path(path)
        
    def select_objects(self, objs):
        for obj in objs: self.select_object(obj, False)
        
    def add_object(self, new_object):
        if new_object:
            cur_obj = self.get_selected_object()
            if cur_obj:
                index = self.liststore.index(cur_obj)
                self.liststore.insert(index+1, new_object)
            else:
                self.liststore.append(new_object)
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    
    def on_item_removed(self, model, item):
        pass
        
    def on_item_inserted(self, model, item):
        pass
    
    def objects_tv_selection_changed(self, selection):        
        obj = self.get_selected_object()
        objs = self.get_selected_objects()
        self.set_object_sensitivities((obj!=None or objs!=None))
        if self.edit_controller==None or obj!=self.edit_controller.model:
            self.edit_object(obj)

    def on_load_object_clicked(self, event):
        raise NotImplementedError

    def on_save_object_clicked(self, event):
        raise NotImplementedError

    def create_new_object_proxy(self):
        raise NotImplementedError

    def on_add_object_clicked(self, event):
        new_object = self.create_new_object_proxy()
        if new_object:
            self.add_object(new_object)
            self.select_object(new_object)
        return True

    def on_del_object_clicked(self, event, del_callback=None, callback=None):
        tv = self.view.treeview
        selection = tv.get_selection()
        if selection.count_selected_rows() >= 1:
            def delete_objects(dialog):
                for obj in self.get_selected_objects():
                    if callable(del_callback):
                        del_callback(obj)
                    else:
                        self.liststore.remove_item(obj)
                    if callable(callback): callback(obj)
                self.set_object_sensitivities(False)
                self.edit_object(None)
            self.run_confirmation_dialog(message=self.delete_msg, on_accept_callback=delete_objects, parent=self.view.get_top_widget())

        
class ObjectListStoreController(DialogController, ObjectListStoreMixin):
    """
        A stand-alone, regular ObjectListStore controller (left pane with objects and right pane with object properties)
    """
    title="Edit Dialog"
  
    def __init__(self, model, view,
                 spurious=False, auto_adapt=False, parent=None,
                 model_property_name="", columns=[], delete_msg="", title=""):
        DialogController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        ObjectListStoreMixin.__init__(self, model_property_name=model_property_name, columns=columns, delete_msg=delete_msg)        
        self.title = title or self.title
        view.set_title(self.title)
        
    def register_adapters(self):
        ObjectListStoreMixin.register_adapters(self)
            
class ChildObjectListStoreController(BaseController, ObjectListStoreMixin):
    """
        An embedable, regular ObjectListStore controller (left pane with objects and right pane with object properties)
    """
    def __init__(self, model, view,
                 spurious=False, auto_adapt=False, parent=None,
                 model_property_name="", columns=[], delete_msg=""):
        BaseController.__init__(self, model, view, spurious=spurious, auto_adapt=auto_adapt, parent=parent)
        ObjectListStoreMixin.__init__(self, model_property_name=model_property_name, columns=columns, delete_msg=delete_msg)
        
    def register_adapters(self):
        ObjectListStoreMixin.register_adapters(self)

class InlineObjectListStoreController(BaseController, ObjectTreeviewMixin):
    """
        ObjectListStore controller that consists of a single listview, 
        with import & export and add & delete buttons and an optional combo box
        for type selection
        Subclasses should override the _setup_treeview method to setup their 
        columns and edit support.
    """
    treeview = None
    enable_import = True
    enable_export = True
    model_property_name = ""
    add_types = list()
    
    @property
    def liststore(self):
        return getattr(self.model, self.model_property_name)

    def _edit_item(self, item):
        item_type = type(item)
        for name, tpe, view, ctrl in self.add_types:
            if tpe==item_type:
                vw = view()
                ct = ctrl(model=item, view=vw, parent=self)
                vw.present()
                break

    def _setup_combo_type(self, combo):
        if self.add_types:
            store = gtk.ListStore(str, object, object, object)   
            for name, type, view, ctrl in self.add_types:
                store.append([name, type, view, ctrl])
                
            combo.set_model(store)

            cell = gtk.CellRendererText()
            combo.pack_start(cell, True)
            combo.add_attribute(cell, 'text', 0)
            
            def on_changed(combo, user_data=None):
                itr = combo.get_active_iter()
                if itr != None:
                    val = combo.get_model().get_value(itr, 1)
                    self.add_type = val
            combo.connect('changed', on_changed)
            combo.set_active_iter(store[0].iter)
            combo.set_visible(True)
            combo.set_no_show_all(False)
            combo.show_all()

    def _setup_treeview(self, tv, model):
        raise NotImplementedError

    def __init__(self, model_property_name, enable_import=True, enable_export=True, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)
        self.enable_import = enable_import
        self.enable_export = enable_export
        self.model_property_name = model_property_name

    def register_adapters(self):
        if self.liststore is not None:
            self.treeview = self.view.treeview_widget
            self.treeview.connect('cursor-changed', self.on_treeview_cursor_changed, self.liststore)
            self._setup_treeview(self.treeview, self.liststore)
            self.type_combobox = self.view.type_combobox_widget
            self._setup_combo_type(self.type_combobox)
        self.update_sensitivities()
        return

    def update_sensitivities(self):
        self.view.del_item_widget.set_sensitive((self.treeview.get_cursor() != (None, None)))
        self.view.add_item_widget.set_sensitive((self.liststore is not None))
        self.view.export_items_widget.set_visible(self.enable_export)
        self.view.export_items_widget.set_sensitive(len(self.liststore) > 0)        
        self.view.import_items_widget.set_visible(self.enable_import)

    def get_selected_object(self):
        return ObjectTreeviewMixin.get_selected_object(self, self.treeview)
        
    def get_selected_objects(self):
        return ObjectTreeviewMixin.get_selected_objects(self, self.treeview)
        
    def get_all_objects(self):
        return ObjectTreeviewMixin.get_all_objects(self, self.treeview)
    
    def select_object(self, obj, unselect_all=True):
        selection = self.treeview.get_selection()
        if unselect_all: selection.unselect_all()
        if hasattr(self.liststore, "on_get_path"):
            selection.select_path(self.liststore.on_get_path(obj))
    
    def create_new_object_proxy(self):
        raise NotImplementedError
        
    # ------------------------------------------------------------
    #      GTK Signal handlers
    # ------------------------------------------------------------
    def on_treeview_cursor_changed(self, widget, model):
        self.update_sensitivities()

    def on_add_item(self, widget, user_data=None):
        new_object = self.create_new_object_proxy()
        if new_object != None:
            self.liststore.append(new_object)
            self.select_object(new_object)
        self.update_sensitivities()

    def on_del_item(self, widget, user_data=None):
        path, col = self.treeview.get_cursor()
        if path != None:
            itr = self.liststore.get_iter(path)
            self.liststore.remove(itr)
            self.update_sensitivities()
            return True
        return False

    def on_export_item(self, widget, user_data=None):
        raise NotImplementedError
        
    def on_import_item(self, widget, user_data=None):        
        raise NotImplementedError

    def on_item_cell_edited(self, cell, path, new_text, model, col):
        model.set_value(model.get_iter(path), col, model.convert(col, new_text))
        pass
        
    pass #end of class