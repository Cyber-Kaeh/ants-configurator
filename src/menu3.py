from prompt_toolkit import Application
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, ConditionalContainer
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.filters import Condition, has_focus
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Frame


STYLE = Style.from_dict({
    "art":                "fg:#ffaa00 bold",
    "title":              "fg:#00afff bold",
    "menu-item":          "fg:#ffffff",
    "menu-item.selected": "fg:#ffaa00 bold",
    "toolbar":            "bg:#333333 fg:#aaaaaa",
    "frame.border":       "fg:#0088ff",
    "frame.label":        "fg:#0088ff bold",
    "output-line":        "fg:#cccccc",
    "output-empty":       "fg:#555555 italic",
    "input-prompt":       "fg:#ffffff",
    "input-field":        "bg:#0d1117 fg:#ffffff",
})


class Menu:
    def __init__(self, title, commands, startup_art=None):
        self.title = title
        self.commands = commands
        self.startup_art = startup_art


class MenuApp:
    def __init__(self, extra_bindings=None):
        self._current_menu = None
        self._selected_index = 0
        self._art = None
        self._output_lines: list[str] = []

        self._input_active = False
        self._input_prompt_text = ""
        self._input_callback = None

        self._text_area = TextArea(
            multiline=False,
            style="class:input-field",
            focusable=True,
        )

        # Output panel — BufferControl-backed so scrollbar, mouse-wheel,
        # and text selection all work natively.
        self._output_area = TextArea(
            text="",
            read_only=True,
            scrollbar=True,
            wrap_lines=True,
            focusable=True,
            style="class:output-line",
        )

        kb = KeyBindings()
        not_in_input = ~Condition(lambda: self._input_active)
        in_input     =  Condition(lambda: self._input_active)
        has_output   =  Condition(lambda: bool(self._output_lines))
        in_output    = has_focus(self._output_area)
        panel_active = Condition(lambda: self._input_active or bool(self._output_lines))

        # Menu navigation only fires when neither input nor output panel is focused.
        menu_active = not_in_input & ~in_output

        @kb.add("up", filter=menu_active)
        def _up(_event):
            if self._current_menu:
                n = len(self._current_menu.commands)
                self._selected_index = (self._selected_index - 1) % n

        @kb.add("down", filter=menu_active)
        def _down(_event):
            if self._current_menu:
                n = len(self._current_menu.commands)
                self._selected_index = (self._selected_index + 1) % n

        @kb.add("enter", filter=menu_active)
        def _enter(_event):
            if not self._current_menu:
                return
            keys = list(self._current_menu.commands.keys())
            if not keys:
                return
            _, action = self._current_menu.commands[keys[self._selected_index]]
            self._output_lines.clear()
            self._output_area.buffer.set_document(Document(""), bypass_readonly=True)
            action()

        @kb.add("enter", filter=in_input)
        def _input_submit(_event):
            value = self._text_area.text
            self._text_area.text = ""
            self._input_active = False
            callback = self._input_callback
            self._input_callback = None
            self._app.layout.focus(self._menu_window)
            if callback:
                callback(value)

        @kb.add("escape", filter=in_input)
        def _input_cancel(_event):
            self._text_area.text = ""
            self._input_active = False
            self._input_callback = None
            self._app.layout.focus(self._menu_window)

        # Tab shifts focus to the output panel for scrolling / text selection,
        # Tab again (or Escape) returns focus to the menu.
        @kb.add("tab", filter=not_in_input)
        def _tab(_event):
            if self._output_lines:
                if in_output():
                    self._app.layout.focus(self._menu_window)
                else:
                    self._app.layout.focus(self._output_area)

        @kb.add("escape", filter=in_output)
        def _output_escape(_event):
            self._app.layout.focus(self._menu_window)

        all_bindings = (
            merge_key_bindings([kb, extra_bindings]) if extra_bindings else kb
        )

        def get_art():
            if self._art and isinstance(self._art, str):
                return FormattedText([("class:art", self._art)])
            return FormattedText([])

        def get_title():
            if self._current_menu:
                return FormattedText([("class:title", f"\n  {self._current_menu.title}\n\n")])
            return FormattedText([])

        def get_menu():
            if not self._current_menu:
                return FormattedText([])
            tokens = []
            for i, (key, (label, action)) in enumerate(self._current_menu.commands.items()):
                def make_click_handler(idx, act):
                    def handler(mouse_event):
                        from prompt_toolkit.mouse_events import MouseEventType
                        if mouse_event.event_type == MouseEventType.MOUSE_UP:
                            self._selected_index = idx
                            self._app.layout.focus(self._menu_window)
                            act()
                    return handler

                style = "class:menu-item.selected" if i == self._selected_index else "class:menu-item"
                prefix = "  > " if i == self._selected_index else "    "
                tokens.append((style, f"{prefix}{key}) {label}\n", make_click_handler(i, action)))
            return FormattedText(tokens)

        def get_toolbar():
            return HTML(
                "  <title>↑↓</title> navigate  <title>Enter</title> select  "
                "<title>b</title> back  <title>h</title> home  "
                "<title>t</title> toggle  <title>qq</title> quit  "
                "<title>Tab</title> scroll output  <title>Esc</title> exit input/output"
            )

        # dont_extend_width=True: Window reports its natural content width (longest
        # menu-item line) as a fixed int to VSplit, so the right panel gets the rest.
        self._menu_window = Window(
            FormattedTextControl(get_menu, focusable=True, show_cursor=False),
            dont_extend_width=True,
        )

        right_content = HSplit([
            # Input mode
            ConditionalContainer(
                HSplit([
                    Window(
                        FormattedTextControl(lambda: f"  {self._input_prompt_text}"),
                        dont_extend_height=True,
                        style="class:input-prompt",
                    ),
                    self._text_area,
                    Window(),  # expands to fill frame height, keeping toolbar pinned
                ]),
                filter=in_input,
            ),
            # Output placeholder (no lines yet)
            ConditionalContainer(
                Window(
                    FormattedTextControl(
                        lambda: FormattedText([("class:output-empty", "\n  No output yet.")])
                    ),
                ),
                filter=not_in_input & ~has_output,
            ),
            # Output panel (BufferControl: scrollbar + text selection work)
            ConditionalContainer(
                self._output_area,
                filter=not_in_input & has_output,
            ),
        ])

        # Right panel: framed (with blue border) when active, blank spacer when idle.
        # Both options are the same width so the menu never reflows.
        # Right panel fills all space not consumed by the menu column.
        # Removing fixed widths lets both containers return None (expanding)
        # so the outer VSplit gives everything left-over to this side.
        right_panel = VSplit([
            ConditionalContainer(
                Frame(
                    right_content,
                    title=lambda: "  Input  " if self._input_active else "  Output  ",
                ),
                filter=panel_active,
            ),
            ConditionalContainer(
                Window(),
                filter=~panel_active,
            ),
        ])

        main_content = HSplit([
            Window(FormattedTextControl(get_art), dont_extend_height=True),
            VSplit([
                HSplit([
                    Window(FormattedTextControl(get_title), dont_extend_height=True),
                    self._menu_window,
                ]),
                right_panel,
            ]),
            Window(FormattedTextControl(get_toolbar), height=1, style="class:toolbar"),
        ])

        layout = Layout(main_content, focused_element=self._menu_window)

        self._app = Application(
            layout=layout,
            key_bindings=all_bindings,
            style=STYLE,
            full_screen=True,
            mouse_support=True,
        )

    def request_input(self, prompt_text, callback):
        """Show the input panel. callback(value) on Enter, callback(None) on Escape."""
        self._input_prompt_text = prompt_text
        self._input_callback = callback
        self._input_active = True
        self._text_area.text = ""
        self._app.layout.focus(self._text_area)
        self._app.invalidate()

    def add_output(self, message: str):
        """Append a line to the output panel and auto-scroll to the bottom."""
        self._output_lines.append(message)
        text = "\n".join(f"  {line}" for line in self._output_lines)
        self._output_area.buffer.set_document(
            Document(text, cursor_position=len(text)),
            bypass_readonly=True,
        )
        self._app.invalidate()

    @property
    def current_menu(self):
        return self._current_menu

    @current_menu.setter
    def current_menu(self, menu):
        if self._art is None and menu.startup_art and isinstance(menu.startup_art, str):
            self._art = menu.startup_art
        self._current_menu = menu
        self._selected_index = 0
        self._app.invalidate()

    def run(self):
        self._app.run()
