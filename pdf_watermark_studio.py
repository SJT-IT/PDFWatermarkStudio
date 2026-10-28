import os
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser

import customtkinter as ctk
import fitz  # PyMuPDF


APP_NAME = "PDF Watermark Studio"

POSITIONS = {
    "Top left": (0.18, 0.18),
    "Top center": (0.50, 0.18),
    "Top right": (0.82, 0.18),
    "Middle left": (0.18, 0.50),
    "Center": (0.50, 0.50),
    "Middle right": (0.82, 0.50),
    "Bottom left": (0.18, 0.82),
    "Bottom center": (0.50, 0.82),
    "Bottom right": (0.82, 0.82),
}
ALL_POSITIONS = "All 9 positions"

# Windows 11-inspired palette
COLORS = {
    "light": {
        "window": "#F3F5F9",
        "surface": "#FFFFFF",
        "surface_alt": "#F7F9FC",
        "border": "#E3E7EF",
        "text": "#202633",
        "muted": "#697586",
        "accent": "#0866D9",
        "accent_hover": "#0757B8",
        "success": "#16834A",
        "error": "#C93636",
        "track": "#E3E9F2",
    },
    "dark": {
        "window": "#17191E",
        "surface": "#22252C",
        "surface_alt": "#292D35",
        "border": "#383D48",
        "text": "#F1F3F8",
        "muted": "#A5ADBC",
        "accent": "#60A5FA",
        "accent_hover": "#3B82F6",
        "success": "#4ADE80",
        "error": "#F87171",
        "track": "#3A404C",
    },
}


class PDFWatermarkStudio:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("940x900")
        self.root.minsize(760, 760)

        self.theme = "light"
        self.c = COLORS[self.theme]

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.watermark_text = tk.StringVar(value="CONFIDENTIAL")
        self.font_size = tk.IntVar(value=40)
        self.opacity = tk.DoubleVar(value=25)
        self.rotation = tk.IntVar(value=45)
        self.position = tk.StringVar(value=ALL_POSITIONS)
        self.pages_mode = tk.StringVar(value="All")
        self.page_range = tk.StringVar()
        self.layer = tk.StringVar(value="Over document")

        self.color_rgb = (0.65, 0.65, 0.65)
        self.color_hex = "#A6A6A6"
        self.busy = False

        ctk.set_appearance_mode("light")
        self.root.configure(bg=self.c["window"])

        self.build_ui()
        self.opacity.trace_add("write", self.update_opacity_label)
        self.update_range_state()
        self.refresh_theme()

    # ---------- UI helpers ----------

    def card(self, parent, title, subtitle=None):
        frame = ctk.CTkFrame(
            parent,
            fg_color=self.c["surface"],
            border_color=self.c["border"],
            border_width=1,
            corner_radius=14,
        )
        frame.pack(fill="x", pady=(0, 14))

        heading = ctk.CTkFrame(frame, fg_color="transparent")
        heading.pack(fill="x", padx=18, pady=(15, 8))

        ctk.CTkLabel(
            heading,
            text=title,
            font=("Segoe UI", 15, "bold"),
            text_color=self.c["text"],
        ).pack(anchor="w")

        if subtitle:
            ctk.CTkLabel(
                heading,
                text=subtitle,
                font=("Segoe UI", 11),
                text_color=self.c["muted"],
            ).pack(anchor="w", pady=(3, 0))

        body = ctk.CTkFrame(frame, fg_color="transparent")
        body.pack(fill="x", padx=18, pady=(0, 16))
        return body

    def label(self, parent, text, **kwargs):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=("Segoe UI", 12),
            text_color=self.c["text"],
            **kwargs,
        )

    def entry(self, parent, variable, placeholder=""):
        return ctk.CTkEntry(
            parent,
            textvariable=variable,
            placeholder_text=placeholder,
            height=38,
            corner_radius=8,
            border_width=1,
            fg_color=self.c["surface_alt"],
            border_color=self.c["border"],
            text_color=self.c["text"],
            placeholder_text_color=self.c["muted"],
            font=("Segoe UI", 12),
        )

    def button(self, parent, text, command, primary=False, width=None):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width or 120,
            height=38,
            corner_radius=8,
            font=("Segoe UI", 12, "bold" if primary else "normal"),
            fg_color=self.c["accent"] if primary else self.c["surface_alt"],
            hover_color=(
                self.c["accent_hover"] if primary
                else self.c["border"]
            ),
            text_color="#FFFFFF" if primary else self.c["text"],
            border_width=0 if primary else 1,
            border_color=self.c["border"],
        )

    def option_menu(self, parent, variable, values):
        return ctk.CTkOptionMenu(
            parent,
            variable=variable,
            values=values,
            height=38,
            corner_radius=8,
            fg_color=self.c["surface_alt"],
            button_color=self.c["border"],
            button_hover_color=self.c["accent"],
            text_color=self.c["text"],
            dropdown_fg_color=self.c["surface"],
            dropdown_text_color=self.c["text"],
            dropdown_hover_color=self.c["surface_alt"],
            font=("Segoe UI", 12),
            dynamic_resizing=False,
        )

    # ---------- Build the interface ----------

    def build_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(
            self.root,
            fg_color=self.c["window"],
            corner_radius=0,
            scrollbar_button_color=self.c["border"],
        )
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        main = ctk.CTkFrame(self.scroll, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28, pady=24)

        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 22))

        heading = ctk.CTkFrame(header, fg_color="transparent")
        heading.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            heading,
            text="PDF Watermark Studio",
            font=("Segoe UI", 27, "bold"),
            text_color=self.c["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            heading,
            text="Protect your documents with a custom watermark.",
            font=("Segoe UI", 13),
            text_color=self.c["muted"],
        ).pack(anchor="w", pady=(4, 0))

        self.theme_button = ctk.CTkButton(
            header,
            text="☾  Dark mode",
            command=self.toggle_theme,
            width=125,
            height=36,
            corner_radius=9,
            fg_color=self.c["surface"],
            hover_color=self.c["surface_alt"],
            text_color=self.c["text"],
            border_width=1,
            border_color=self.c["border"],
            font=("Segoe UI", 11),
        )
        self.theme_button.pack(side="right", padx=(12, 0), pady=5)

        # 1. Files
        files = self.card(
            main,
            "01  |  PDF files",
            "Choose the source document and where to save the result.",
        )

        self.label(files, "Input PDF").pack(anchor="w", pady=(0, 5))

        input_row = ctk.CTkFrame(files, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 14))

        self.entry(
            input_row, self.input_path, "Select a PDF document..."
        ).pack(side="left", fill="x", expand=True)

        self.button(
            input_row, "Browse", self.choose_input, width=100
        ).pack(side="left", padx=(8, 0))

        self.label(files, "Output location").pack(
            anchor="w", pady=(0, 5)
        )

        output_row = ctk.CTkFrame(files, fg_color="transparent")
        output_row.pack(fill="x")

        self.entry(
            output_row, self.output_path, "Choose the output filename..."
        ).pack(side="left", fill="x", expand=True)

        self.button(
            output_row, "Browse", self.choose_output, width=100
        ).pack(side="left", padx=(8, 0))

        # 2. Watermark appearance
        appearance = self.card(
            main,
            "02  |  Watermark appearance",
            "Customize the text, styling, and placement.",
        )

        appearance.grid_columnconfigure(1, weight=1)
        appearance.grid_columnconfigure(3, weight=1)

        self.label(appearance, "Watermark text").grid(
            row=0, column=0, sticky="w", pady=(0, 12), padx=(0, 12)
        )
        self.entry(
            appearance, self.watermark_text, "e.g. CONFIDENTIAL"
        ).grid(
            row=0, column=1, columnspan=3,
            sticky="ew", pady=(0, 12)
        )

        self.label(appearance, "Font size").grid(
            row=1, column=0, sticky="w", pady=(0, 12), padx=(0, 12)
        )
        self.font_spin = ctk.CTkEntry(
            appearance,
            textvariable=self.font_size,
            width=100,
            height=38,
            corner_radius=8,
            fg_color=self.c["surface_alt"],
            border_color=self.c["border"],
            text_color=self.c["text"],
        )
        self.font_spin.grid(
            row=1, column=1, sticky="w", pady=(0, 12)
        )

        self.label(appearance, "Rotation").grid(
            row=1, column=2, sticky="w", pady=(0, 12), padx=(16, 12)
        )
        self.rotation_spin = ctk.CTkEntry(
            appearance,
            textvariable=self.rotation,
            width=100,
            height=38,
            corner_radius=8,
            fg_color=self.c["surface_alt"],
            border_color=self.c["border"],
            text_color=self.c["text"],
        )
        self.rotation_spin.grid(
            row=1, column=3, sticky="w", pady=(0, 12)
        )

        self.label(appearance, "Opacity").grid(
            row=2, column=0, sticky="w", padx=(0, 12), pady=(0, 12)
        )

        opacity_frame = ctk.CTkFrame(
            appearance, fg_color="transparent"
        )
        opacity_frame.grid(
            row=2, column=1, columnspan=3,
            sticky="ew", pady=(0, 12)
        )
        opacity_frame.grid_columnconfigure(0, weight=1)

        self.opacity_slider = ctk.CTkSlider(
            opacity_frame,
            from_=5,
            to=100,
            variable=self.opacity,
            command=self.update_opacity_label,
            height=18,
            button_color=self.c["accent"],
            button_hover_color=self.c["accent_hover"],
            progress_color=self.c["accent"],
            fg_color=self.c["track"],
        )
        self.opacity_slider.grid(
            row=0, column=0, sticky="ew", padx=(0, 14)
        )

        self.opacity_label = self.label(
            opacity_frame, "25%", width=45
        )
        self.opacity_label.grid(row=0, column=1, sticky="e")

        self.label(appearance, "Text color").grid(
            row=3, column=0, sticky="w", padx=(0, 12), pady=(0, 12)
        )

        color_frame = ctk.CTkFrame(
            appearance, fg_color="transparent"
        )
        color_frame.grid(
            row=3, column=1, sticky="w", pady=(0, 12)
        )

        self.color_swatch = ctk.CTkFrame(
            color_frame,
            width=25,
            height=25,
            corner_radius=6,
            fg_color=self.color_hex,
            border_width=1,
            border_color=self.c["border"],
        )
        self.color_swatch.pack(side="left", padx=(0, 8))
        self.color_swatch.pack_propagate(False)

        self.color_button = self.button(
            color_frame, self.color_hex, self.choose_color, width=110
        )
        self.color_button.pack(side="left")

        self.label(appearance, "Position").grid(
            row=3, column=2, sticky="w", padx=(16, 12), pady=(0, 12)
        )
        self.option_menu(
            appearance, self.position, list(POSITIONS) + [ALL_POSITIONS]
        ).grid(row=3, column=3, sticky="ew", pady=(0, 12))

        self.label(appearance, "Layer").grid(
            row=4, column=0, sticky="w", padx=(0, 12)
        )
        self.option_menu(
            appearance,
            self.layer,
            ["Over document", "Behind document"],
        ).grid(row=4, column=1, columnspan=3, sticky="ew")

        # 3. Page selection
        pages = self.card(
            main,
            "03  |  Page selection",
            "Choose which pages receive the watermark.",
        )

        self.pages_segment = ctk.CTkSegmentedButton(
            pages,
            values=["All pages", "Specific pages"],
            command=self.on_pages_mode_changed,
            selected_color=self.c["accent"],
            selected_hover_color=self.c["accent_hover"],
            unselected_color=self.c["surface_alt"],
            unselected_hover_color=self.c["border"],
            text_color=self.c["text"],
            height=38,
            corner_radius=8,
            font=("Segoe UI", 12),
        )
        self.pages_segment.pack(anchor="w", pady=(0, 14))
        self.pages_segment.set("All pages")
        self.label(
            pages, "Page numbers (example: 1-3, 5, 8-10)"
        ).pack(anchor="w", pady=(0, 5))

        self.range_entry = self.entry(
            pages,
            self.page_range,
            "e.g. 1-3, 5, 8-10",
        )
        self.range_entry.pack(fill="x")

        # 4. Progress and actions
        actions = self.card(
            main,
            "04  |  Apply watermark",
            "Review your settings and create the watermarked PDF.",
        )

        self.progress_label = self.label(
            actions, "Ready to process."
        )
        self.progress_label.pack(anchor="w", pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            actions,
            height=8,
            corner_radius=5,
            progress_color=self.c["accent"],
            fg_color=self.c["track"],
        )
        self.progress_bar.pack(fill="x", pady=(0, 16))
        self.progress_bar.set(0)

        self.process_button = self.button(
            actions,
            "Apply watermark",
            self.start_processing,
            primary=True,
        )
        self.process_button.pack(fill="x")

        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 10))

        self.label(
            footer,
            "PDF Watermark Studio",
        ).pack(anchor="center")

    # ---------- File selection ----------

    def choose_input(self):
        path = filedialog.askopenfilename(
            title="Select input PDF",
            filetypes=[("PDF documents", "*.pdf")],
        )

        if path:
            self.input_path.set(path)

            base, _ = os.path.splitext(path)
            self.output_path.set(base + "_watermarked.pdf")

    def choose_output(self):
        path = filedialog.asksaveasfilename(
            title="Save watermarked PDF",
            defaultextension=".pdf",
            filetypes=[("PDF documents", "*.pdf")],
            initialfile="watermarked.pdf",
        )

        if path:
            self.output_path.set(path)

    # ---------- Appearance ----------

    def choose_color(self):
        result = colorchooser.askcolor(
            color=self.color_hex,
            title="Choose watermark text color",
            parent=self.root,
        )

        if result and result[1]:
            self.color_hex = result[1]
            rgb = result[0]

            self.color_rgb = tuple(
                component / 255 for component in rgb
            )

            self.color_swatch.configure(
                fg_color=self.color_hex
            )
            self.color_button.configure(
                text=self.color_hex
            )

    def update_opacity_label(self, *_):
        value = self.opacity.get()
        self.opacity_label.configure(
            text=f"{round(value)}%"
        )

    def toggle_theme(self):
        self.theme = (
            "dark" if self.theme == "light" else "light"
        )
        self.c = COLORS[self.theme]

        ctk.set_appearance_mode(self.theme)
        self.root.configure(bg=self.c["window"])

        self.theme_button.configure(
            text=(
                "☀  Light mode"
                if self.theme == "dark"
                else "☾  Dark mode"
            )
        )

        # Rebuild the UI to apply the selected theme.
        # Preserve all current settings.
        self.scroll.destroy()
        self.build_ui()
        self.refresh_theme()
        self.update_range_state()
        self.update_opacity_label()

    def refresh_theme(self):
        self.root.configure(bg=self.c["window"])

    # ---------- Page selection ----------

    def on_pages_mode_changed(self, value):
        self.pages_mode.set(
            "All" if value == "All pages" else "Specific"
        )
        self.update_range_state()

    def update_range_state(self):
        if not hasattr(self, "range_entry"):
            return

        if self.pages_mode.get() == "Specific":
            self.range_entry.configure(state="normal")
        else:
            self.range_entry.configure(state="disabled")

    # ---------- Validation ----------

    def parse_page_range(self, text, page_count):
        """
        Parse page numbers such as:
        1-3, 5, 8-10

        Page numbers are 1-based.
        """
        if not text.strip():
            raise ValueError(
                "Enter the page numbers to watermark."
            )

        selected = set()

        for part in text.split(","):
            part = part.strip()

            if not part:
                raise ValueError(
                    "Invalid page range. Check for empty entries."
                )

            if "-" in part:
                pieces = part.split("-")

                if len(pieces) != 2:
                    raise ValueError(
                        f"Invalid page range: {part}"
                    )

                try:
                    start = int(pieces[0].strip())
                    end = int(pieces[1].strip())
                except ValueError:
                    raise ValueError(
                        f"Invalid page range: {part}"
                    )

                if start < 1 or end < start:
                    raise ValueError(
                        f"Invalid page range: {part}"
                    )

                if end > page_count:
                    raise ValueError(
                        f"Page {end} exceeds the document's "
                        f"{page_count} pages."
                    )

                selected.update(range(start - 1, end))

            else:
                try:
                    page = int(part)
                except ValueError:
                    raise ValueError(
                        f"Invalid page number: {part}"
                    )

                if page < 1 or page > page_count:
                    raise ValueError(
                        f"Page {page} is outside the valid range "
                        f"1-{page_count}."
                    )

                selected.add(page - 1)

        return sorted(selected)

    def validate_inputs(self):
        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()
        watermark = self.watermark_text.get().strip()

        if not input_path:
            raise ValueError("Please select an input PDF.")

        if not os.path.isfile(input_path):
            raise ValueError("The selected input file does not exist.")

        if not input_path.lower().endswith(".pdf"):
            raise ValueError("The input file must be a PDF.")

        if not output_path:
            raise ValueError("Please select an output filename.")

        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"
            self.output_path.set(output_path)

        if os.path.abspath(input_path) == os.path.abspath(output_path):
            raise ValueError(
                "Input and output paths must be different."
            )

        if not watermark:
            raise ValueError("Enter the watermark text.")

        try:
            font_size = int(self.font_size.get())
            rotation = int(self.rotation.get())
            opacity = float(self.opacity.get())
        except (ValueError, tk.TclError):
            raise ValueError(
                "Font size, rotation, or opacity is invalid."
            )

        if not 1 <= font_size <= 300:
            raise ValueError("Font size must be between 1 and 300.")

        if not -360 <= rotation <= 360:
            raise ValueError(
                "Rotation must be between -360 and 360 degrees."
            )

        if not 5 <= opacity <= 100:
            raise ValueError("Opacity must be between 5% and 100%.")

        output_dir = os.path.dirname(
            os.path.abspath(output_path)
        )

        if not os.path.isdir(output_dir):
            raise ValueError(
                "The output directory does not exist."
            )

        return {
            "input_path": input_path,
            "output_path": output_path,
            "watermark": watermark,
            "font_size": font_size,
            "rotation": rotation,
            "opacity": opacity / 100.0,
        }

    # ---------- PDF watermarking ----------

    def add_watermark(self, page, settings):
        text = settings["watermark"]
        font_size = settings["font_size"]
        rotation = settings["rotation"]
        opacity = settings["opacity"]

        page_rect = page.rect

        positions = (
            list(POSITIONS.values())
            if settings["position"] == ALL_POSITIONS
            else [POSITIONS[settings["position"]]]
        )

        color = settings["color_rgb"]

        # Estimate the text dimensions using the standard PDF font.
        font = fitz.Font("helv")
        text_width = font.text_length(
            text,
            fontsize=font_size,
        )

        text_height = font_size * 1.2

        # Use a transparent overlay so watermark opacity is supported.
        overlay = fitz.open()
        overlay_page = overlay.new_page(
            width=page_rect.width,
            height=page_rect.height,
        )

        for x_ratio, y_ratio in positions:
            center_x = page_rect.width * x_ratio
            center_y = page_rect.height * y_ratio

            # Center the watermark around the target point.
            point = fitz.Point(
                center_x - text_width / 2,
                center_y + font_size * 0.35,
            )

            # Draw text with opacity and rotation.
            overlay_page.insert_text(
                point,
                text,
                fontname="helv",
                fontsize=font_size,
                color=color,
                fill_opacity=opacity,
                stroke_opacity=opacity,
                rotate=rotation,
                overlay=True,
            )

        # Merge the watermark overlay with the original page.
        page.show_pdf_page(
            page_rect,
            overlay,
            0,
            overlay=(settings["layer"] == "Over document"),
        )


        overlay.close()

    def process_pdf(self, settings):
        input_path = settings["input_path"]
        output_path = settings["output_path"]

        source_doc = None
        output_doc = None
        temp_path = None

        try:
            source_doc = fitz.open(input_path)

            if source_doc.is_encrypted:
                if not source_doc.authenticate(""):
                    raise ValueError(
                        "The PDF is password-protected. "
                        "Please provide an unlocked PDF."
                    )

            page_count = len(source_doc)

            if page_count == 0:
                raise ValueError("The input PDF contains no pages.")

            if settings["pages_mode"] == "Specific":
                selected_pages = self.parse_page_range(
                    settings["page_range"],
                    page_count,
                )
            else:
                selected_pages = list(range(page_count))
            selected_set = set(selected_pages)

            # Work on a separate document so the source remains intact.
            output_doc = fitz.open()
            output_doc.insert_pdf(source_doc)

            # Create a temporary output file in the destination directory.
            output_dir = os.path.dirname(
                os.path.abspath(output_path)
            )

            fd, temp_path = tempfile.mkstemp(
                suffix=".pdf",
                prefix=".watermark_",
                dir=output_dir,
            )
            os.close(fd)

            total = len(selected_pages)

            for index, page_number in enumerate(selected_pages):
                page = output_doc[page_number]

                self.add_watermark(page, settings)

                progress = (index + 1) / total if total else 1
                self.root.after(
                    0,
                    self.update_progress,
                    progress,
                    f"Processing page {page_number + 1} of {page_count}...",
                )

            # Save to the temporary file first.
            output_doc.save(
                temp_path,
                garbage=4,
                deflate=True,
                clean=True,
            )

            output_doc.close()
            output_doc = None

            source_doc.close()
            source_doc = None

            # Replace the destination only after a successful save.
            os.replace(temp_path, output_path)
            temp_path = None

            self.root.after(
                0,
                self.processing_finished,
                output_path,
            )

        except Exception as exc:
            self.root.after(
                0,
                self.processing_failed,
                str(exc),
            )

        finally:
            if output_doc is not None:
                output_doc.close()

            if source_doc is not None:
                source_doc.close()

            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    # ---------- Processing controls ----------

    def start_processing(self):
        if self.busy:
            return

        try:
            settings = self.validate_inputs()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror(
                "Invalid settings",
                str(exc),
                parent=self.root,
            )
            return

        # Capture the current page-selection settings before starting.
        settings["pages_mode"] = self.pages_mode.get()
        settings["page_range"] = self.page_range.get()
        settings["position"] = self.position.get()
        settings["layer"] = self.layer.get()
        settings["color_rgb"] = self.color_rgb

        self.busy = True
        self.process_button.configure(
            state="disabled",
            text="Processing...",
        )
        self.progress_bar.set(0)
        self.progress_label.configure(
            text="Preparing your PDF..."
        )

        worker = threading.Thread(
            target=self.process_pdf,
            args=(settings,),
            daemon=True,
        )
        worker.start()

    def update_progress(self, value, message):
        self.progress_bar.set(value)
        self.progress_label.configure(text=message)

    def processing_finished(self, output_path):
        self.busy = False

        self.process_button.configure(
            state="normal",
            text="Apply watermark",
        )
        self.progress_bar.set(1)
        self.progress_label.configure(
            text="Watermark applied successfully."
        )

        messagebox.showinfo(
            "Success",
            f"Your watermarked PDF has been saved to:\n\n"
            f"{output_path}",
            parent=self.root,
        )

    def processing_failed(self, error):
        self.busy = False

        self.process_button.configure(
            state="normal",
            text="Apply watermark",
        )
        self.progress_label.configure(
            text="Processing failed.",
            text_color=self.c["error"],
        )

        self.progress_bar.set(0)

        messagebox.showerror(
            "Processing error",
            f"Could not watermark the PDF:\n\n{error}",
            parent=self.root,
        )


if __name__ == "__main__":
    root = ctk.CTk()
    app = PDFWatermarkStudio(root)
    root.mainloop()
