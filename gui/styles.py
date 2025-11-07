"""
GUI Styling and Theme Configuration

Provides consistent styling for all GUI components using tkinter.ttk.
Defines colors, fonts, and custom styles for professional appearance.
"""

import tkinter as tk
from tkinter import ttk


class StyleManager:
    """Manages GUI styling and theme configuration"""

    # Color scheme (professional blue/gray theme)
    COLORS = {
        'primary': '#2c3e50',      # Dark blue-gray
        'secondary': '#34495e',    # Lighter blue-gray
        'accent': '#3498db',       # Blue accent
        'success': '#27ae60',      # Green
        'warning': '#f39c12',      # Orange
        'error': '#e74c3c',        # Red
        'background': '#ecf0f1',   # Light gray
        'text': '#2c3e50',         # Dark text
        'light_text': '#7f8c8d',   # Lighter text
    }

    # Font configurations
    FONTS = {
        'default': ('Arial', 9),
        'heading': ('Arial', 12, 'bold'),
        'title': ('Arial', 16, 'bold'),
        'subtitle': ('Arial', 10),
        'mono': ('Consolas', 9),
    }

    # Widget styling configuration
    WIDGET_CONFIGS = {
        'TFrame': {
            'background': COLORS['background']
        },
        'TLabel': {
            'background': COLORS['background'],
            'foreground': COLORS['text'],
            'font': FONTS['default']
        },
        'TButton': {
            'font': FONTS['default'],
            'padding': (10, 6)
        },
        'TEntry': {
            'fieldbackground': 'white',
            'borderwidth': 1,
            'relief': 'solid'
        },
        'TNotebook': {
            'tabmargins': (0, 0, 0, 0)
        },
        'TNotebook.Tab': {
            'padding': [12, 8],
            'font': FONTS['default']
        }
    }

    @classmethod
    def configure_style(cls, root=None):
        """Configure ttk styles for the application

        Args:
            root: tkinter root window (optional)
        """
        style = ttk.Style()

        # Try to set a modern theme if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')

        # Configure custom styles
        cls._configure_button_styles(style)
        cls._configure_frame_styles(style)
        cls._configure_label_styles(style)
        cls._configure_notebook_styles(style)

    @classmethod
    def _configure_button_styles(cls, style):
        """Configure button styles"""
        # Default button
        style.configure(
            'TButton',
            font=cls.FONTS['default'],
            padding=(10, 6),
            relief='raised'
        )

        # Primary action button (e.g., Convert, Process)
        style.configure(
            'Primary.TButton',
            font=cls.FONTS['default'],
            padding=(12, 8),
            foreground='white',
            background=cls.COLORS['accent'],
            relief='raised'
        )

        # Browse button
        style.configure(
            'Browse.TButton',
            font=cls.FONTS['default'],
            padding=(8, 4)
        )

    @classmethod
    def _configure_frame_styles(cls, style):
        """Configure frame styles"""
        style.configure(
            'TFrame',
            background=cls.COLORS['background'],
            relief='flat'
        )

        # Title frame style
        style.configure(
            'Title.TFrame',
            background=cls.COLORS['primary'],
            relief='raised'
        )

    @classmethod
    def _configure_label_styles(cls, style):
        """Configure label styles"""
        style.configure(
            'TLabel',
            background=cls.COLORS['background'],
            foreground=cls.COLORS['text'],
            font=cls.FONTS['default']
        )

        # Title label
        style.configure(
            'Title.TLabel',
            font=cls.FONTS['title'],
            foreground=cls.COLORS['primary']
        )

        # Heading label
        style.configure(
            'Heading.TLabel',
            font=cls.FONTS['heading'],
            foreground=cls.COLORS['text']
        )

        # Subtitle label
        style.configure(
            'Subtitle.TLabel',
            font=cls.FONTS['subtitle'],
            foreground=cls.COLORS['light_text']
        )

        # Success label
        style.configure(
            'Success.TLabel',
            foreground=cls.COLORS['success']
        )

        # Error label
        style.configure(
            'Error.TLabel',
            foreground=cls.COLORS['error']
        )

    @classmethod
    def _configure_notebook_styles(cls, style):
        """Configure notebook (tab) styles"""
        style.configure(
            'TNotebook',
            background=cls.COLORS['background'],
            tabmargins=(0, 0, 0, 0)
        )

        style.configure(
            'TNotebook.Tab',
            padding=[12, 8],
            font=cls.FONTS['default'],
            background=cls.COLORS['secondary'],
            foreground='white'
        )

        # Selected tab
        style.map(
            'TNotebook.Tab',
            background=[('selected', cls.COLORS['primary'])],
            foreground=[('selected', 'white')]
        )


def apply_default_styling(root):
    """Apply default styling to a tkinter root window

    Args:
        root: tkinter root window
    """
    # Configure ttk styles
    StyleManager.configure_style(root)

    # Set default window background
    root.configure(background=StyleManager.COLORS['background'])


def create_styled_label(parent, text, style='TLabel', **kwargs):
    """Create a styled label with common defaults

    Args:
        parent: Parent widget
        text: Label text
        style: ttk style to use
        **kwargs: Additional arguments for ttk.Label

    Returns:
        ttk.Label widget
    """
    return ttk.Label(parent, text=text, style=style, **kwargs)


def create_styled_button(parent, text, command=None, style='TButton', **kwargs):
    """Create a styled button with common defaults

    Args:
        parent: Parent widget
        text: Button text
        command: Button command function
        style: ttk style to use
        **kwargs: Additional arguments for ttk.Button

    Returns:
        ttk.Button widget
    """
    return ttk.Button(parent, text=text, command=command, style=style, **kwargs)