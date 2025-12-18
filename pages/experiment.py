# pages/experiment.py
from nicegui import ui
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Global lab book storage
lab_entries = []
current_entry = None

def load_lab_book():
    """Load lab book entries from JSON file"""
    global lab_entries
    lab_book_file = 'data/lab_book.json'

    if os.path.exists(lab_book_file):
        try:
            with open(lab_book_file, 'r', encoding='utf-8') as f:
                lab_entries = json.load(f)
        except Exception as e:
            print(f"Error loading lab book: {e}")
            lab_entries = []
    else:
        lab_entries = []

def save_lab_book():
    """Save lab book entries to JSON file"""
    lab_book_file = 'data/lab_book.json'
    os.makedirs('data', exist_ok=True)

    try:
        with open(lab_book_file, 'w', encoding='utf-8') as f:
            json.dump(lab_entries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving lab book: {e}")

def create_new_entry():
    """Create a new lab book entry"""
    return {
        'id': f"entry_{int(datetime.now().timestamp() * 1000)}",
        'date': datetime.now().strftime("%Y-%m-%d"),
        'time': datetime.now().strftime("%H:%M"),
        'title': '',
        'objective': '',
        'procedure': '',
        'observations': '',
        'results': '',
        'conclusion': '',
        'tags': [],
        'attachments': [],
        'created': datetime.now().isoformat(),
        'modified': datetime.now().isoformat()
    }

def export_entry_to_markdown(entry):
    """Export lab book entry to markdown format"""
    md = f"""# {entry['title']}

**Date:** {entry['date']} {entry['time']}
**Entry ID:** {entry['id']}
**Tags:** {', '.join(entry['tags']) if entry['tags'] else 'None'}

---

## Objective
{entry['objective'] if entry['objective'] else '_No objective recorded_'}

---

## Procedure
{entry['procedure'] if entry['procedure'] else '_No procedure recorded_'}

---

## Observations
{entry['observations'] if entry['observations'] else '_No observations recorded_'}

---

## Results
{entry['results'] if entry['results'] else '_No results recorded_'}

---

## Conclusion
{entry['conclusion'] if entry['conclusion'] else '_No conclusion recorded_'}

---

_Created: {entry['created']}_
_Last Modified: {entry['modified']}_
"""
    return md

def render():
    """Render the experiment/lab book page content"""
    global lab_entries

    # Load lab book
    load_lab_book()

    with ui.column().style("padding: 20px; width: 100%; gap: 20px; height: calc(100vh - 80px); overflow-y: auto;"):
        # Header
        with ui.row().style("width: 100%; justify-content: space-between; align-items: center; margin-bottom: 10px;"):
            with ui.column().style("gap: 5px;"):
                ui.label("Laboratory Notebook").style("color: white; font-size: 24px; font-weight: bold;")
                ui.label("Document experiments, observations, and results").style("color: #888888; font-size: 14px;")

            # Search and filter
            with ui.row().style("gap: 10px;"):
                search_input = ui.input(placeholder="Search entries...").props("dark outlined dense").style("width: 250px;")

                def show_new_entry_dialog():
                    """Show dialog to create a new entry"""
                    new_entry = create_new_entry()

                    with ui.dialog() as dialog, ui.card().style("background-color: #333333; padding: 20px; min-width: 500px;"):
                        ui.label("New Lab Book Entry").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                        title_input = ui.input(label="Title", placeholder="e.g., Synthesis of Compound X").props("dark outlined").style("width: 100%; margin-bottom: 10px;")
                        title_input.on_value_change(lambda e: new_entry.update({'title': e.value}))

                        tags_input = ui.input(label="Tags (comma-separated)", placeholder="e.g., synthesis, organic, compound-x").props("dark outlined").style("width: 100%; margin-bottom: 15px;")

                        with ui.row().style("gap: 10px; width: 100%; justify-content: flex-end;"):
                            ui.button("Cancel", on_click=dialog.close).props("flat color=white")

                            def create_entry():
                                if not new_entry['title']:
                                    ui.notify("Please enter a title", type='warning')
                                    return

                                # Parse tags
                                if tags_input.value:
                                    new_entry['tags'] = [tag.strip() for tag in tags_input.value.split(',') if tag.strip()]

                                lab_entries.insert(0, new_entry)  # Add to beginning
                                save_lab_book()
                                ui.notify(f"Created entry: {new_entry['title']}", type='positive')

                                # Refresh the entry list
                                render_entry_list()

                                dialog.close()

                                # Use timer to show editor after dialog closes
                                ui.timer(0.1, lambda: show_entry_editor(new_entry), once=True)

                            ui.button("Create", icon="add", on_click=create_entry).props("color=primary")

                    dialog.open()

                ui.button("New Entry", icon="add", on_click=show_new_entry_dialog).props("color=primary")

        # Main content - Entry list
        with ui.row().style("width: 100%; gap: 20px;"):
            # Left column - Entry list (scrollable)
            with ui.column().style("flex: 0 0 350px; gap: 10px; max-height: calc(100vh - 200px); overflow-y: auto;"):
                entries_container = ui.column().style("gap: 10px; width: 100%;")

                def render_entry_list(search_term=''):
                    """Render the list of lab book entries"""
                    entries_container.clear()

                    with entries_container:
                        if lab_entries:
                            filtered_entries = lab_entries
                            if search_term:
                                search_lower = search_term.lower()
                                filtered_entries = [e for e in lab_entries if
                                    search_lower in e['title'].lower() or
                                    search_lower in e.get('objective', '').lower() or
                                    search_lower in e.get('observations', '').lower() or
                                    any(search_lower in tag.lower() for tag in e.get('tags', []))
                                ]

                            if filtered_entries:
                                for entry in filtered_entries:
                                    with ui.card().style("background-color: #333333; padding: 15px; cursor: pointer; border-left: 3px solid #1976d2;").on('click', lambda e=entry: show_entry_editor(e)):
                                        # Title and date
                                        ui.label(entry['title']).style("color: white; font-size: 16px; font-weight: bold; margin-bottom: 5px;")
                                        ui.label(f"{entry['date']} {entry['time']}").style("color: #888888; font-size: 12px; margin-bottom: 8px;")

                                        # Tags
                                        if entry.get('tags'):
                                            with ui.row().style("gap: 5px; flex-wrap: wrap; margin-bottom: 5px;"):
                                                for tag in entry['tags']:
                                                    ui.label(tag).style("background-color: #1976d2; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;")

                                        # Preview of objective
                                        if entry.get('objective'):
                                            preview = entry['objective'][:80] + "..." if len(entry['objective']) > 80 else entry['objective']
                                            ui.label(preview).style("color: #aaaaaa; font-size: 13px; font-style: italic;")
                            else:
                                ui.label(f"No entries found matching '{search_term}'").style("color: #888888; font-size: 14px; padding: 20px;")
                        else:
                            ui.label("No entries yet. Click 'New Entry' to start.").style("color: #888888; font-size: 14px; padding: 20px;")

                # Initial render
                render_entry_list()

                # Search functionality
                search_input.on_value_change(lambda e: render_entry_list(e.value))

            # Right column - Entry preview/empty state
            with ui.column().style("flex: 1; background-color: #333333; border-radius: 8px; padding: 30px; align-items: center; justify-content: center;"):
                ui.icon("book", size="64px").style("color: #555555; margin-bottom: 15px;")
                ui.label("Select an entry to view or edit").style("color: #888888; font-size: 16px;")
                ui.label("Or create a new entry to get started").style("color: #666666; font-size: 14px;")

def show_entry_editor(entry):
    """Show full-screen entry editor"""
    with ui.dialog().props('maximized') as editor_dialog:
        with ui.card().style("background-color: #222222; padding: 0; width: 100%; height: 100%;"):
            # Header bar
            with ui.row().style("background-color: #333333; padding: 15px 20px; width: 100%; justify-content: space-between; align-items: center;"):
                with ui.column().style("gap: 5px;"):
                    ui.label(entry['title'] or "Untitled Entry").style("color: white; font-size: 20px; font-weight: bold;")
                    ui.label(f"{entry['date']} {entry['time']}").style("color: #888888; font-size: 14px;")

                with ui.row().style("gap: 10px;"):
                    def export_entry():
                        """Export entry to markdown file"""
                        try:
                            filename = f"{entry['date']}_{entry['title'].replace(' ', '_')}.md"
                            filepath = os.path.join('data', 'exports', filename)
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)

                            markdown = export_entry_to_markdown(entry)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(markdown)

                            ui.notify(f"Exported to {filename}", type='positive')
                        except Exception as e:
                            ui.notify(f"Export error: {str(e)}", type='negative')

                    def delete_entry():
                        """Delete the current entry"""
                        if entry in lab_entries:
                            lab_entries.remove(entry)
                            save_lab_book()
                            ui.notify("Entry deleted", type='info')
                            editor_dialog.close()

                    ui.button("Export", icon="download", on_click=export_entry).props("flat color=white")
                    ui.button("Delete", icon="delete", on_click=delete_entry).props("flat color=negative")
                    ui.button(icon="close", on_click=editor_dialog.close).props("flat color=white")

            # Main content - Scrollable form
            with ui.column().style("flex: 1; padding: 30px; overflow-y: auto; max-width: 1200px; margin: 0 auto; width: 100%;"):
                # Entry metadata section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-bottom: 20px;"):
                    ui.label("Entry Information").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 15px;")

                    with ui.row().style("gap: 20px; width: 100%; margin-bottom: 15px;"):
                        # Title
                        title_edit = ui.input(label="Title", value=entry['title']).props("dark outlined").style("flex: 1;")
                        title_edit.on_value_change(lambda e: update_entry(entry, 'title', e.value))

                        # Date
                        date_edit = ui.input(label="Date", value=entry['date']).props("dark outlined").style("width: 150px;")
                        date_edit.on_value_change(lambda e: update_entry(entry, 'date', e.value))

                        # Time
                        time_edit = ui.input(label="Time", value=entry['time']).props("dark outlined").style("width: 120px;")
                        time_edit.on_value_change(lambda e: update_entry(entry, 'time', e.value))

                    # Tags
                    tags_str = ', '.join(entry.get('tags', []))
                    tags_edit = ui.input(label="Tags (comma-separated)", value=tags_str, placeholder="e.g., synthesis, organic, analysis").props("dark outlined").style("width: 100%;")

                    def update_tags(e):
                        entry['tags'] = [tag.strip() for tag in e.value.split(',') if tag.strip()]
                        update_entry(entry, 'tags', entry['tags'])

                    tags_edit.on_value_change(update_tags)

                # Objective section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-bottom: 20px;"):
                    ui.label("Objective").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
                    ui.label("What is the goal of this experiment?").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                    objective_edit = ui.textarea(value=entry.get('objective', ''), placeholder="Describe the purpose and goals...").props("dark outlined").style("width: 100%; min-height: 100px;")
                    objective_edit.on_value_change(lambda e: update_entry(entry, 'objective', e.value))

                # Procedure section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-bottom: 20px;"):
                    ui.label("Procedure").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
                    ui.label("Step-by-step experimental procedure").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                    procedure_edit = ui.textarea(value=entry.get('procedure', ''), placeholder="1. First step...\n2. Second step...\n3. Third step...").props("dark outlined").style("width: 100%; min-height: 150px;")
                    procedure_edit.on_value_change(lambda e: update_entry(entry, 'procedure', e.value))

                # Observations section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-bottom: 20px;"):
                    ui.label("Observations").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
                    ui.label("What did you observe during the experiment?").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                    observations_edit = ui.textarea(value=entry.get('observations', ''), placeholder="Note any observations, changes, unexpected events...").props("dark outlined").style("width: 100%; min-height: 150px;")
                    observations_edit.on_value_change(lambda e: update_entry(entry, 'observations', e.value))

                # Results section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-bottom: 20px;"):
                    ui.label("Results").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
                    ui.label("Quantitative and qualitative results").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                    results_edit = ui.textarea(value=entry.get('results', ''), placeholder="Record measurements, data, yields, analysis...").props("dark outlined").style("width: 100%; min-height: 150px;")
                    results_edit.on_value_change(lambda e: update_entry(entry, 'results', e.value))

                # Conclusion section
                with ui.card().style("background-color: #333333; padding: 20px; width: 100%; margin-bottom: 20px;"):
                    ui.label("Conclusion").style("color: white; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
                    ui.label("Interpretation and implications").style("color: #888888; font-size: 13px; margin-bottom: 10px;")

                    conclusion_edit = ui.textarea(value=entry.get('conclusion', ''), placeholder="Summarize findings, success/failure, next steps...").props("dark outlined").style("width: 100%; min-height: 100px;")
                    conclusion_edit.on_value_change(lambda e: update_entry(entry, 'conclusion', e.value))

                # Timestamp info
                ui.label(f"Created: {entry['created']}").style("color: #666666; font-size: 12px; margin-top: 20px;")
                ui.label(f"Last Modified: {entry.get('modified', entry['created'])}").style("color: #666666; font-size: 12px;")

    editor_dialog.open()

def update_entry(entry, field, value):
    """Update an entry field and save"""
    entry[field] = value
    entry['modified'] = datetime.now().isoformat()
    save_lab_book()
