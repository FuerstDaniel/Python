import sqlite3
import csv
import os
import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# PDF export
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except ModuleNotFoundError:
    REPORTLAB_AVAILABLE = False


APP_TITLE = "Sauschießen – Auswertung"
DB_FILE = "sauschiessen.db"

# Business rules
ENTRY_FEE_EUR = 15.00
REB_PURCHASE_SERIES_EUR = 3.00          # Glück/Meister: 10 shots
REB_PURCHASE_SAU_SHOT_EUR = 1.00        # Saukönig: 1 shot
SAU_INCLUDED_SHOTS = 3
SAU_MAX_EXTRA_SHOTS = 5                 # max Nachkauf shots

SHOTS_PER_SERIES = 10

# Meister scoring mode:
# "BEST_SERIES" => rank by best single 10-shot series sum
# "TOTAL_SUM"   => rank by sum of all Meister shots
MEISTER_SCORING_MODE = "BEST_SERIES"


def money(x: float) -> str:
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def now_iso() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Repo:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shooters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                club TEXT NOT NULL,
                wants_glueck INTEGER NOT NULL DEFAULT 0,
                wants_meister INTEGER NOT NULL DEFAULT 0,
                wants_saukoenig INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                shooter_id INTEGER PRIMARY KEY,
                glueck_series_purchased INTEGER NOT NULL DEFAULT 0,
                meister_series_purchased INTEGER NOT NULL DEFAULT 0,
                sau_extra_shots_purchased INTEGER NOT NULL DEFAULT 0,
                entry_fee_paid INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (shooter_id) REFERENCES shooters(id) ON DELETE CASCADE
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS shots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shooter_id INTEGER NOT NULL,
                discipline TEXT NOT NULL,           -- GLUECK | MEISTER | SAU
                series_no INTEGER NOT NULL,          -- 1..n (for SAU we keep series_no=1)
                shot_no INTEGER NOT NULL,            -- 1..10 (or 1..N for SAU)
                value REAL NOT NULL,                 -- Teiler for GLUECK/SAU (smaller is better), Score for MEISTER (higher is better)
                created_at TEXT NOT NULL,
                FOREIGN KEY (shooter_id) REFERENCES shooters(id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    # --- shooters ---
    def add_shooter(self, first_name: str, last_name: str, club: str, wants_glueck: bool, wants_meister: bool, wants_sau: bool) -> int:
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO shooters (first_name, last_name, club, wants_glueck, wants_meister, wants_saukoenig, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name.strip(), last_name.strip(), club.strip(),
              1 if wants_glueck else 0, 1 if wants_meister else 0, 1 if wants_sau else 0, now_iso()))
        shooter_id = cur.lastrowid

        # Base purchase: entry fee includes exactly one 10-shot series (Glück or Meister) and 3 Sau shots.
        glueck_series = 1 if wants_glueck else 0
        meister_series = 1 if wants_meister else 0

        # If both selected, second series must be paid as rebuy (+3 EUR) -> we store it as purchased too.
        # This keeps "purchased" aligned with what they intend to shoot.
        if wants_glueck and wants_meister:
            # both are already 1; the extra cost will be computed in billing.
            pass

        cur.execute("""
            INSERT INTO purchases (shooter_id, glueck_series_purchased, meister_series_purchased, sau_extra_shots_purchased, entry_fee_paid)
            VALUES (?, ?, ?, 0, 1)
        """, (shooter_id, glueck_series, meister_series))
        self.conn.commit()
        return shooter_id

    def delete_shooter(self, shooter_id: int):
        self.conn.execute("DELETE FROM shooters WHERE id = ?", (shooter_id,))
        self.conn.commit()

    def list_shooters(self):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.id, s.first_name, s.last_name, s.club,
                   s.wants_glueck, s.wants_meister, s.wants_saukoenig,
                   p.glueck_series_purchased, p.meister_series_purchased, p.sau_extra_shots_purchased
            FROM shooters s
            JOIN purchases p ON p.shooter_id = s.id
            ORDER BY s.last_name, s.first_name;
        """)
        return cur.fetchall()

    def get_shooter(self, shooter_id: int):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.id, s.first_name, s.last_name, s.club,
                   s.wants_glueck, s.wants_meister, s.wants_saukoenig,
                   p.glueck_series_purchased, p.meister_series_purchased, p.sau_extra_shots_purchased
            FROM shooters s
            JOIN purchases p ON p.shooter_id = s.id
            WHERE s.id = ?;
        """, (shooter_id,))
        return cur.fetchone()

    # --- purchases (rebuy) ---
    def buy_series(self, shooter_id: int, discipline: str):
        if discipline not in ("GLUECK", "MEISTER"):
            raise ValueError("discipline must be GLUECK or MEISTER")
        col = "glueck_series_purchased" if discipline == "GLUECK" else "meister_series_purchased"
        self.conn.execute(f"UPDATE purchases SET {col} = {col} + 1 WHERE shooter_id = ?;", (shooter_id,))
        self.conn.commit()

    def can_buy_sau_shot(self, shooter_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT sau_extra_shots_purchased FROM purchases WHERE shooter_id = ?;", (shooter_id,))
        row = cur.fetchone()
        if not row:
            return False
        return row[0] < SAU_MAX_EXTRA_SHOTS

    def buy_sau_shot(self, shooter_id: int) -> bool:
        if not self.can_buy_sau_shot(shooter_id):
            return False
        self.conn.execute("""
            UPDATE purchases
            SET sau_extra_shots_purchased = sau_extra_shots_purchased + 1
            WHERE shooter_id = ?;
        """, (shooter_id,))
        self.conn.commit()
        return True

    # --- shots ---
    def count_shots(self, shooter_id: int, discipline: str) -> int:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM shots
            WHERE shooter_id = ? AND discipline = ?;
        """, (shooter_id, discipline))
        return int(cur.fetchone()[0])

    def allowed_shots(self, shooter_id: int, discipline: str) -> int:
        shooter = self.get_shooter(shooter_id)
        if not shooter:
            return 0
        _, _, _, _, _, _, _, glueck_p, meister_p, sau_extra = shooter

        if discipline == "GLUECK":
            return glueck_p * SHOTS_PER_SERIES
        if discipline == "MEISTER":
            return meister_p * SHOTS_PER_SERIES
        if discipline == "SAU":
            return SAU_INCLUDED_SHOTS + sau_extra
        return 0

    def add_shot(self, shooter_id: int, discipline: str, series_no: int, shot_no: int, value: float):
        if discipline not in ("GLUECK", "MEISTER", "SAU"):
            raise ValueError("Invalid discipline")
        # Capacity validation
        current = self.count_shots(shooter_id, discipline)
        allowed = self.allowed_shots(shooter_id, discipline)
        if current >= allowed:
            raise ValueError(f"Keine weiteren Schüsse erlaubt für {discipline}. (aktuell {current}/{allowed})")

        self.conn.execute("""
            INSERT INTO shots (shooter_id, discipline, series_no, shot_no, value, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (shooter_id, discipline, series_no, shot_no, float(value), now_iso()))
        self.conn.commit()

    def list_shots(self, shooter_id: int, discipline: str):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT series_no, shot_no, value, created_at
            FROM shots
            WHERE shooter_id = ? AND discipline = ?
            ORDER BY series_no, shot_no, id;
        """, (shooter_id, discipline))
        return cur.fetchall()

    # --- scoring / ranking ---
    def glueck_best_teiler(self, shooter_id: int):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT MIN(value) FROM shots
            WHERE shooter_id = ? AND discipline = 'GLUECK';
        """, (shooter_id,))
        v = cur.fetchone()[0]
        return v

    def sau_best_teiler(self, shooter_id: int):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT MIN(value) FROM shots
            WHERE shooter_id = ? AND discipline = 'SAU';
        """, (shooter_id,))
        v = cur.fetchone()[0]
        return v

    def meister_points(self, shooter_id: int):
        cur = self.conn.cursor()
        if MEISTER_SCORING_MODE == "TOTAL_SUM":
            cur.execute("""
                SELECT SUM(value) FROM shots
                WHERE shooter_id = ? AND discipline = 'MEISTER';
            """, (shooter_id,))
            v = cur.fetchone()[0]
            return v

        # BEST_SERIES: sum per series, take max
        cur.execute("""
            SELECT series_no, SUM(value) AS s
            FROM shots
            WHERE shooter_id = ? AND discipline = 'MEISTER'
            GROUP BY series_no
            ORDER BY s DESC
            LIMIT 1;
        """, (shooter_id,))
        row = cur.fetchone()
        return row[1] if row else None

    def all_rankings(self):
        shooters = self.list_shooters()

        glueck = []
        meister = []
        sau = []

        for s in shooters:
            sid, fn, ln, club, wants_g, wants_m, wants_sau, _, _, _ = s
            name = f"{fn} {ln}"
            if wants_g:
                bt = self.glueck_best_teiler(sid)
                if bt is not None:
                    glueck.append((bt, sid, name, club))
            if wants_m:
                pts = self.meister_points(sid)
                if pts is not None:
                    meister.append((pts, sid, name, club))
            if wants_sau:
                bt = self.sau_best_teiler(sid)
                if bt is not None:
                    sau.append((bt, sid, name, club))

        glueck.sort(key=lambda x: x[0])      # min teiler wins
        sau.sort(key=lambda x: x[0])         # min teiler wins
        meister.sort(key=lambda x: x[0], reverse=True)  # max points wins

        return glueck, meister, sau

    # --- billing ---
    def compute_costs(self, shooter_id: int) -> float:
        shooter = self.get_shooter(shooter_id)
        if not shooter:
            return 0.0
        _, _, _, _, wants_g, wants_m, _, glueck_p, meister_p, sau_extra = shooter

        total = 0.0
        total += ENTRY_FEE_EUR

        # Entry includes exactly one 10-shot series.
        # If they selected both Glück and Meister initially, second one costs +3 EUR.
        if wants_g and wants_m:
            total += REB_PURCHASE_SERIES_EUR

        # Additional series beyond the initial included ones:
        # We assume initial included series are reflected by wants_* (0/1).
        included_glueck = 1 if wants_g else 0
        included_meister = 1 if wants_m else 0

        extra_glueck = max(0, glueck_p - included_glueck)
        extra_meister = max(0, meister_p - included_meister)

        total += (extra_glueck + extra_meister) * REB_PURCHASE_SERIES_EUR
        total += sau_extra * REB_PURCHASE_SAU_SHOT_EUR

        return total

    # --- exports ---
    def export_csv(self, path: str):
        shooters = self.list_shooters()
        glueck, meister, sau = self.all_rankings()

        # summary CSV
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["ShooterId", "FirstName", "LastName", "Club",
                        "WantsGlueck", "WantsMeister", "WantsSau",
                        "GlueckSeriesPurchased", "MeisterSeriesPurchased", "SauExtraShotsPurchased",
                        "GlueckBestTeiler", "MeisterPoints", "SauBestTeiler", "TotalCostEUR"])

            for s in shooters:
                sid, fn, ln, club, wants_g, wants_m, wants_sau, gp, mp, sau_extra = s
                bt_g = self.glueck_best_teiler(sid) if wants_g else None
                pts_m = self.meister_points(sid) if wants_m else None
                bt_s = self.sau_best_teiler(sid) if wants_sau else None
                cost = self.compute_costs(sid)

                w.writerow([sid, fn, ln, club, wants_g, wants_m, wants_sau, gp, mp, sau_extra,
                            bt_g, pts_m, bt_s, f"{cost:.2f}"])

    def export_pdf(self, path: str):
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("PDF Export benötigt das Paket 'reportlab'. Installation: python -m pip install reportlab")
        shooters = self.list_shooters()
        glueck, meister, sau = self.all_rankings()

        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4

        def header(title: str):
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20 * mm, height - 20 * mm, title)
            c.setFont("Helvetica", 9)
            c.drawString(20 * mm, height - 26 * mm, f"Export: {now_iso()}")

        def line(y):
            c.line(20 * mm, y, width - 20 * mm, y)

        y = height - 35 * mm
        header("Sauschießen – Ergebnisliste")

        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y, "Teilnehmer / Übersicht")
        y -= 4 * mm
        line(y)
        y -= 6 * mm

        c.setFont("Helvetica", 8)
        cols = ["Name", "Verein", "Glück (best)", "Meister (pts)", "Saukönig (best)", "Nachkauf G/M", "Nachkauf Sau", "Kosten"]
        col_x = [20, 60, 105, 130, 155, 180, 200, 220]  # mm
        for i, htxt in enumerate(cols):
            c.drawString(col_x[i] * mm, y, htxt)
        y -= 4 * mm
        line(y)
        y -= 6 * mm

        for s in shooters:
            sid, fn, ln, club, wants_g, wants_m, wants_sau, gp, mp, sau_extra = s
            name = f"{fn} {ln}"
            bt_g = self.glueck_best_teiler(sid) if wants_g else None
            pts_m = self.meister_points(sid) if wants_m else None
            bt_s = self.sau_best_teiler(sid) if wants_sau else None
            cost = self.compute_costs(sid)

            gtxt = f"{bt_g:.1f}" if bt_g is not None else "-"
            mtxt = f"{pts_m:.1f}" if pts_m is not None else "-"
            stxt = f"{bt_s:.1f}" if bt_s is not None else "-"

            # purchased vs included to show "Nachkauf"
            incl_g = 1 if wants_g else 0
            incl_m = 1 if wants_m else 0
            extra_gm = max(0, gp - incl_g) + max(0, mp - incl_m)

            row = [name, club, gtxt, mtxt, stxt, str(extra_gm), str(sau_extra), money(cost)]
            for i, txt in enumerate(row):
                c.drawString(col_x[i] * mm, y, txt)
            y -= 5 * mm

            if y < 30 * mm:
                c.showPage()
                header("Sauschießen – Ergebnisliste (Fortsetzung)")
                y = height - 35 * mm

        # Rankings
        c.showPage()
        header("Sauschießen – Platzierungen")

        def ranking_block(title: str, rows: list, y_start: float, kind: str):
            y = y_start
            c.setFont("Helvetica-Bold", 11)
            c.drawString(20 * mm, y, title)
            y -= 4 * mm
            line(y)
            y -= 7 * mm
            c.setFont("Helvetica", 9)
            c.drawString(20 * mm, y, "Platz")
            c.drawString(35 * mm, y, "Name")
            c.drawString(110 * mm, y, "Verein")
            c.drawString(170 * mm, y, "Wert")
            y -= 4 * mm
            line(y)
            y -= 7 * mm

            c.setFont("Helvetica", 9)
            for idx, r in enumerate(rows[:25], start=1):
                val, _, name, club = r
                if kind == "TEILER":
                    vtxt = f"{val:.1f}"
                else:
                    vtxt = f"{val:.1f}"
                c.drawString(20 * mm, y, str(idx))
                c.drawString(35 * mm, y, name)
                c.drawString(110 * mm, y, club)
                c.drawRightString(190 * mm, y, vtxt)
                y -= 6 * mm
                if y < 25 * mm:
                    c.showPage()
                    header("Sauschießen – Platzierungen (Fortsetzung)")
                    y = height - 35 * mm
            return y

        y = height - 35 * mm
        y = ranking_block("Glücksserie – bester Teiler (kleiner ist besser)", glueck, y, "TEILER")
        y -= 8 * mm
        y = ranking_block("Meisterserie – Punkte (größer ist besser)", meister, y, "PTS")
        y -= 8 * mm
        _ = ranking_block("Saukönig – bester Teiler (kleiner ist besser)", sau, y, "TEILER")

        c.save()


class App(ttk.Frame):
    def __init__(self, master, repo: Repo):
        super().__init__(master)
        self.master = master
        self.repo = repo

        self.master.title(APP_TITLE)
        self.master.geometry("1100x650")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._build_tab_shooters()
        self._build_tab_entry()
        self._build_tab_rankings()
        self._build_tab_export()

        self.pack(fill="both", expand=True)
        self.refresh_all()

    # ---------- UI helpers ----------
    def refresh_all(self):
        self.refresh_shooters_table()
        self.refresh_entry_context()
        self.refresh_rankings()

    def selected_shooter_id(self):
        sel = self.tv_shooters.selection()
        if not sel:
            return None
        return int(self.tv_shooters.item(sel[0], "values")[0])

    # ---------- Tab 1: Shooters ----------
    def _build_tab_shooters(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Schützen")

        frm = ttk.Frame(tab)
        frm.pack(fill="x", padx=10, pady=10)

        self.var_fn = tk.StringVar()
        self.var_ln = tk.StringVar()
        self.var_club = tk.StringVar()
        self.var_g = tk.BooleanVar(value=True)
        self.var_m = tk.BooleanVar(value=False)
        self.var_s = tk.BooleanVar(value=True)

        ttk.Label(frm, text="Vorname").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_fn, width=20).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(frm, text="Nachname").grid(row=0, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_ln, width=20).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(frm, text="Schützenverein").grid(row=0, column=4, sticky="w")
        ttk.Entry(frm, textvariable=self.var_club, width=30).grid(row=0, column=5, padx=5, pady=2)

        ttk.Checkbutton(frm, text="Glücksserie", variable=self.var_g).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Checkbutton(frm, text="Meisterserie", variable=self.var_m).grid(row=1, column=3, sticky="w", pady=2)
        ttk.Checkbutton(frm, text="Saukönig", variable=self.var_s).grid(row=1, column=5, sticky="w", pady=2)

        ttk.Button(frm, text="Schützen anlegen", command=self.on_add_shooter).grid(row=2, column=1, pady=8, sticky="w")
        ttk.Button(frm, text="Schützen löschen", command=self.on_delete_shooter).grid(row=2, column=3, pady=8, sticky="w")
        ttk.Button(frm, text="Aktualisieren", command=self.refresh_all).grid(row=2, column=5, pady=8, sticky="w")

        # table
        self.tv_shooters = ttk.Treeview(tab, columns=(
            "id", "name", "club", "modes", "p_glueck", "p_meister", "p_sau", "cost"
        ), show="headings", height=18)

        heads = {
            "id": "ID",
            "name": "Name",
            "club": "Verein",
            "modes": "Modi",
            "p_glueck": "Glück Serien",
            "p_meister": "Meister Serien",
            "p_sau": "Sau Extra",
            "cost": "Kosten"
        }
        for col in self.tv_shooters["columns"]:
            self.tv_shooters.heading(col, text=heads[col])
            self.tv_shooters.column(col, width=120 if col not in ("name", "club", "modes") else 220, anchor="w")

        self.tv_shooters.column("id", width=60, anchor="center")
        self.tv_shooters.column("p_glueck", width=90, anchor="center")
        self.tv_shooters.column("p_meister", width=95, anchor="center")
        self.tv_shooters.column("p_sau", width=80, anchor="center")
        self.tv_shooters.column("cost", width=95, anchor="e")

        self.tv_shooters.pack(fill="both", expand=True, padx=10, pady=10)

    def on_add_shooter(self):
        fn = self.var_fn.get().strip()
        ln = self.var_ln.get().strip()
        club = self.var_club.get().strip()

        if not fn or not ln or not club:
            messagebox.showerror("Fehler", "Vorname, Nachname und Schützenverein sind Pflichtfelder.")
            return

        wants_g = bool(self.var_g.get())
        wants_m = bool(self.var_m.get())
        wants_s = bool(self.var_s.get())

        if not (wants_g or wants_m):
            # At least one 10-shot discipline to justify entry
            if not messagebox.askyesno("Hinweis", "Weder Glücksserie noch Meisterserie gewählt. Trotzdem anlegen?"):
                return

        self.repo.add_shooter(fn, ln, club, wants_g, wants_m, wants_s)
        self.var_fn.set("")
        self.var_ln.set("")
        self.var_club.set("")
        self.refresh_all()

    def on_delete_shooter(self):
        sid = self.selected_shooter_id()
        if not sid:
            messagebox.showinfo("Info", "Bitte zuerst einen Schützen auswählen.")
            return
        if not messagebox.askyesno("Bestätigung", "Schützen inklusive Ergebnisse wirklich löschen?"):
            return
        self.repo.delete_shooter(sid)
        self.refresh_all()

    def refresh_shooters_table(self):
        for i in self.tv_shooters.get_children():
            self.tv_shooters.delete(i)

        for s in self.repo.list_shooters():
            sid, fn, ln, club, wants_g, wants_m, wants_sau, gp, mp, sau_extra = s
            modes = []
            if wants_g: modes.append("Glück")
            if wants_m: modes.append("Meister")
            if wants_sau: modes.append("Sau")
            cost = self.repo.compute_costs(sid)

            self.tv_shooters.insert("", "end", values=(
                sid, f"{fn} {ln}", club, ", ".join(modes) if modes else "-",
                gp, mp, sau_extra, money(cost)
            ))

    # ---------- Tab 2: Entry ----------
    def _build_tab_entry(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Ergebnisse erfassen")

        top = ttk.Frame(tab)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Schütze (ID)").grid(row=0, column=0, sticky="w")
        self.var_entry_shooter = tk.StringVar()
        self.cb_shooter = ttk.Combobox(top, textvariable=self.var_entry_shooter, width=45, state="readonly")
        self.cb_shooter.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.cb_shooter.bind("<<ComboboxSelected>>", lambda e: self.refresh_entry_context())

        ttk.Label(top, text="Disziplin").grid(row=0, column=2, sticky="w")
        self.var_disc = tk.StringVar(value="GLUECK")
        self.cb_disc = ttk.Combobox(top, textvariable=self.var_disc, width=12, state="readonly",
                                    values=["GLUECK", "MEISTER", "SAU"])
        self.cb_disc.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.cb_disc.bind("<<ComboboxSelected>>", lambda e: self.refresh_entry_context())

        ttk.Label(top, text="SeriesNo").grid(row=1, column=0, sticky="w")
        self.var_series_no = tk.IntVar(value=1)
        ttk.Spinbox(top, from_=1, to=999, textvariable=self.var_series_no, width=8).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(top, text="ShotNo").grid(row=1, column=2, sticky="w")
        self.var_shot_no = tk.IntVar(value=1)
        ttk.Spinbox(top, from_=1, to=999, textvariable=self.var_shot_no, width=8).grid(row=1, column=3, sticky="w", padx=5)

        ttk.Label(top, text="Wert (Teiler oder Punkte)").grid(row=2, column=0, sticky="w")
        self.var_value = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_value, width=20).grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Button(top, text="Schuss speichern", command=self.on_add_shot).grid(row=2, column=3, padx=5, pady=2, sticky="w")

        # Rebuy controls
        reb = ttk.LabelFrame(tab, text="Nachkauf")
        reb.pack(fill="x", padx=10, pady=10)

        self.lbl_rebuy_info = ttk.Label(reb, text="")
        self.lbl_rebuy_info.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=4)

        ttk.Button(reb, text="Nachkauf Glück 10 Schuss (+3€)", command=lambda: self.on_buy_series("GLUECK")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Button(reb, text="Nachkauf Meister 10 Schuss (+3€)", command=lambda: self.on_buy_series("MEISTER")).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(reb, text="Nachkauf Saukönig 1 Schuss (+1€)", command=self.on_buy_sau).grid(row=1, column=2, padx=5, pady=5, sticky="w")
        ttk.Button(reb, text="Aktualisieren", command=self.refresh_entry_context).grid(row=1, column=3, padx=5, pady=5, sticky="w")

        # Shots list
        bottom = ttk.Frame(tab)
        bottom.pack(fill="both", expand=True, padx=10, pady=10)

        self.tv_shots = ttk.Treeview(bottom, columns=("series", "shot", "value", "time"), show="headings", height=16)
        for col, txt, w in [("series", "SeriesNo", 90), ("shot", "ShotNo", 80), ("value", "Wert", 120), ("time", "Zeit", 200)]:
            self.tv_shots.heading(col, text=txt)
            self.tv_shots.column(col, width=w, anchor="w")
        self.tv_shots.pack(fill="both", expand=True)

    def refresh_entry_context(self):
        # populate shooter combobox
        shooters = self.repo.list_shooters()
        items = [f"{s[0]} – {s[1]} {s[2]} ({s[3]})" for s in shooters]
        self.cb_shooter["values"] = items

        # keep selection if possible
        current = self.var_entry_shooter.get()
        if current not in items:
            self.var_entry_shooter.set(items[0] if items else "")

        sid = self._parse_selected_shooter_id()
        disc = self.var_disc.get()

        # update info and shots table
        for i in self.tv_shots.get_children():
            self.tv_shots.delete(i)

        if not sid:
            self.lbl_rebuy_info.config(text="Kein Schütze ausgewählt.")
            return

        shooter = self.repo.get_shooter(sid)
        if not shooter:
            self.lbl_rebuy_info.config(text="Schütze nicht gefunden.")
            return

        _, fn, ln, club, wants_g, wants_m, wants_sau, gp, mp, sau_extra = shooter
        allowed = self.repo.allowed_shots(sid, disc)
        current_cnt = self.repo.count_shots(sid, disc)
        cost = self.repo.compute_costs(sid)

        # rebuy eligibility
        sau_can = self.repo.can_buy_sau_shot(sid)
        self.lbl_rebuy_info.config(text=(
            f"Schütze: {fn} {ln} | Verein: {club} | Disziplin: {disc} | Schüsse: {current_cnt}/{allowed} | "
            f"Saukönig Nachkauf: {sau_extra}/{SAU_MAX_EXTRA_SHOTS} ({'möglich' if sau_can else 'Limit erreicht'}) | "
            f"Kosten aktuell: {money(cost)}"
        ))

        # list shots
        for (series_no, shot_no, value, t) in self.repo.list_shots(sid, disc):
            self.tv_shots.insert("", "end", values=(series_no, shot_no, value, t))

        # auto-suggest next numbers
        if disc == "SAU":
            self.var_series_no.set(1)
            self.var_shot_no.set(current_cnt + 1)
        else:
            # determine next series/shot based on current count
            next_index = current_cnt + 1
            series_no = (next_index - 1) // SHOTS_PER_SERIES + 1
            shot_no = (next_index - 1) % SHOTS_PER_SERIES + 1
            self.var_series_no.set(series_no)
            self.var_shot_no.set(shot_no)

    def _parse_selected_shooter_id(self):
        s = self.var_entry_shooter.get()
        if not s:
            return None
        try:
            return int(s.split("–")[0].strip())
        except Exception:
            return None

    def on_buy_series(self, discipline: str):
        sid = self._parse_selected_shooter_id()
        if not sid:
            messagebox.showinfo("Info", "Bitte zuerst einen Schützen auswählen.")
            return

        self.repo.buy_series(sid, discipline)
        self.refresh_all()

    def on_buy_sau(self):
        sid = self._parse_selected_shooter_id()
        if not sid:
            messagebox.showinfo("Info", "Bitte zuerst einen Schützen auswählen.")
            return
        if not self.repo.buy_sau_shot(sid):
            messagebox.showwarning("Limit", "Saukönig Nachkauf-Limit (5) ist erreicht.")
            return
        self.refresh_all()

    def on_add_shot(self):
        sid = self._parse_selected_shooter_id()
        if not sid:
            messagebox.showinfo("Info", "Bitte zuerst einen Schützen auswählen.")
            return

        disc = self.var_disc.get().strip().upper()
        try:
            series_no = int(self.var_series_no.get())
            shot_no = int(self.var_shot_no.get())
        except Exception:
            messagebox.showerror("Fehler", "SeriesNo/ShotNo müssen Zahlen sein.")
            return

        try:
            val = float(self.var_value.get().replace(",", "."))
        except Exception:
            messagebox.showerror("Fehler", "Wert muss eine Zahl sein. Dezimalpunkt oder Komma sind erlaubt.")
            return

        # basic plausibility (optional)
        if disc in ("GLUECK", "SAU") and val <= 0:
            messagebox.showerror("Fehler", "Teiler muss > 0 sein.")
            return

        try:
            self.repo.add_shot(sid, disc, series_no, shot_no, val)
        except ValueError as e:
            messagebox.showerror("Regel", str(e))
            return

        self.var_value.set("")
        self.refresh_all()

    # ---------- Tab 3: Rankings ----------
    def _build_tab_rankings(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Platzierung")

        info = ttk.Label(tab, text=(
            f"Meister-Wertung: {('Beste Serie' if MEISTER_SCORING_MODE == 'BEST_SERIES' else 'Summe aller Serien')} | "
            "Glück/Sau: kleinster Teiler gewinnt"
        ))
        info.pack(anchor="w", padx=10, pady=5)

        frm = ttk.Frame(tab)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        self.tv_rank_g = ttk.Treeview(frm, columns=("rank", "name", "club", "value"), show="headings", height=12)
        self.tv_rank_m = ttk.Treeview(frm, columns=("rank", "name", "club", "value"), show="headings", height=12)
        self.tv_rank_s = ttk.Treeview(frm, columns=("rank", "name", "club", "value"), show="headings", height=12)

        def setup(tv, title):
            ttk.Label(frm, text=title, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            for col, txt, w in [("rank", "Platz", 60), ("name", "Name", 240), ("club", "Verein", 240), ("value", "Wert", 120)]:
                tv.heading(col, text=txt)
                tv.column(col, width=w, anchor="w")
            tv.column("rank", anchor="center")
            tv.column("value", anchor="e")
            tv.pack(fill="x", pady=(0, 12))

        setup(self.tv_rank_g, "Glücksserie")
        setup(self.tv_rank_m, "Meisterserie")
        setup(self.tv_rank_s, "Saukönig")

    def refresh_rankings(self):
        for tv in (self.tv_rank_g, self.tv_rank_m, self.tv_rank_s):
            for i in tv.get_children():
                tv.delete(i)

        glueck, meister, sau = self.repo.all_rankings()

        for idx, (val, _, name, club) in enumerate(glueck, start=1):
            self.tv_rank_g.insert("", "end", values=(idx, name, club, f"{val:.1f}"))

        for idx, (val, _, name, club) in enumerate(meister, start=1):
            self.tv_rank_m.insert("", "end", values=(idx, name, club, f"{val:.1f}"))

        for idx, (val, _, name, club) in enumerate(sau, start=1):
            self.tv_rank_s.insert("", "end", values=(idx, name, club, f"{val:.1f}"))

    # ---------- Tab 4: Export ----------
    def _build_tab_export(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="Export / Backup")

        frm = ttk.Frame(tab)
        frm.pack(fill="x", padx=10, pady=20)

        ttk.Label(frm, text="CSV und PDF Export erstellen (inkl. Übersicht und Platzierungen).").grid(row=0, column=0, columnspan=3, sticky="w", pady=5)

        ttk.Button(frm, text="CSV exportieren", command=self.on_export_csv).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        ttk.Button(frm, text="PDF exportieren", command=self.on_export_pdf).grid(row=1, column=1, padx=5, pady=10, sticky="w")
        ttk.Button(frm, text="DB-Datei öffnen (Ordner)", command=self.on_open_db_folder).grid(row=1, column=2, padx=5, pady=10, sticky="w")

        hint = ttk.Label(tab, text=f"Datenbank: {os.path.abspath(DB_FILE)}")
        hint.pack(anchor="w", padx=10, pady=5)

    def on_export_csv(self):
        path = filedialog.asksaveasfilename(
            title="CSV exportieren",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")]
        )
        if not path:
            return
        try:
            self.repo.export_csv(path)
            messagebox.showinfo("OK", f"CSV exportiert:\n{path}")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def on_export_pdf(self):
        path = filedialog.asksaveasfilename(
            title="PDF exportieren",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")]
        )
        if not path:
            return
        try:
            self.repo.export_pdf(path)
            messagebox.showinfo("OK", f"PDF exportiert:\n{path}")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def on_open_db_folder(self):
        folder = os.path.dirname(os.path.abspath(DB_FILE))
        try:
            if os.name == "nt":
                os.startfile(folder)
            else:
                messagebox.showinfo("Info", f"Ordner:\n{folder}")
        except Exception:
            messagebox.showinfo("Info", f"Ordner:\n{folder}")


def main():
    repo = Repo(DB_FILE)
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    app = App(root, repo)
    root.mainloop()


if __name__ == "__main__":
    main()
