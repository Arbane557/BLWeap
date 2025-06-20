import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import tkinter as tk
from tkinter import ttk

from part_parser import load_all_parts
from graph_model import build_part_graph
from calc_stat import compute_total_stats

class BLWeapGenerator(tk.Tk):
    FILENAMES = [
        "src/pistols_parts.json",
        "src/smg_parts.json",
        "src/shotguns_parts.json",
        "src/sniper_parts.json",
        "src/rifle_parts.json"
    ]
    FILTERSTATS = [
        ("weaponDamage", "Min Weapon Damage", 0, 50),
        ("accuracy", "Min Accuracy", 0, 100),
        ("fireRate", "Min Fire Rate (shots/sec)", 0, 20),
        ("magSize", "Min Magazine Size", 0, 100),
        ("reloadTime", "Max Reload Time (sec)", 0, 10), 
    ]

    def __init__(self):
        super().__init__()
        
        self.title("BLWeap Generator")
        self.geometry("900x900")
        self.parts = load_all_parts(self.FILENAMES)
        self.graph = build_part_graph(self.parts)
        
        self.all_classes = sorted({p.get("class") for p in self.parts if p.get("class")})
        self.all_manu = sorted({p.get("manufacturer") for p in self.parts if p.get("manufacturer")})
        self.all_element = sorted({p["id"] for p in self.parts if p.get("type") == "element"})
        
        self.create_widgets()
        self.canvas = None

    # Visual
    def create_widgets(self):
        control_frame = ttk.Frame(self)
        control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ttk.Label(control_frame, text="Weapon Class:").grid(row=0, column=0, sticky="w")
        self.class_var = tk.StringVar(value=self.all_classes[0])
        ttk.Combobox(control_frame, textvariable=self.class_var,
                     values=self.all_classes, state="readonly", width=20)\
            .grid(row=0, column=1, sticky="w")

        ttk.Label(control_frame, text="Manufacturer:").grid(row=1, column=0, sticky="w", pady=5)
        self.manu_var = tk.StringVar(value=self.all_manu[0])
        ttk.Combobox(control_frame, textvariable=self.manu_var,
                     values=[""] + self.all_manu, state="readonly", width=20)\
            .grid(row=1, column=1, sticky="w")

        self.match_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Matching manufacturer",
                        variable=self.match_var)\
            .grid(row=2, column=1, sticky="w")

        ttk.Label(control_frame, text="Element:").grid(row=3, column=0, sticky="w", pady=5)
        self.elem_var = tk.StringVar(value=self.all_element[0])
        ttk.Combobox(control_frame, textvariable=self.elem_var,
                     values=[""] + self.all_element, state="readonly", width=20)\
            .grid(row=3, column=1, sticky="w")

        self.stat_vars = {}
        for i, (key, label, minv, maxv) in enumerate(self.FILTERSTATS):
            ttk.Label(control_frame, text=label + ":").grid(row=4+i, column=0, sticky="w", pady=5)
            default = maxv if key == "reloadTime" else minv
            var = tk.DoubleVar(value=default)
            self.stat_vars[key] = var
            tk.Scale(control_frame, variable=var, from_=minv, to=maxv,
                    orient=tk.HORIZONTAL, resolution=1, length=150)\
                .grid(row=4+i, column=1, sticky="w")

        ttk.Button(control_frame, text="Generate Weapon", command=self.generate_weapon)\
            .grid(row=5+len(self.FILTERSTATS), column=0, columnspan=2, pady=10)

        output_frame = ttk.Frame(self)
        output_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.output_box = tk.Text(output_frame, height=15, width=55)
        self.output_box.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        self.graph_frame = ttk.Frame(output_frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)
   

    # Visual
    def draw_subgraph(self, part_ids):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        if not part_ids:
            return

        subgraph = self.graph.subgraph(part_ids)
        pos = nx.spring_layout(subgraph, seed=42, k=0.5)  
        fig, ax = plt.subplots(figsize=(5, 4))
        
        type_colors = {'body': '#FF9999', 'barrel': '#99FF99', 
                      'grip': '#9999FF', 'accessory': '#FFCC99', 'element': '#CC99FF'}
        node_colors = [type_colors.get(self.get_part_type(node), '#CCCCCC') for node in subgraph.nodes()]
        
        nx.draw_networkx_nodes(subgraph, pos, ax=ax, node_size=500, node_color=node_colors, alpha=0.9)
        nx.draw_networkx_edges(subgraph, pos, ax=ax, width=1.5, alpha=0.7)
        nx.draw_networkx_labels(subgraph, pos, font_size=9, ax=ax, font_weight='bold')
        ax.set_axis_off()
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def get_part_type(self, part_id):
        for p in self.parts:
            if p['id'] == part_id:
                return p.get('type', 'unknown')
        return 'unknown'

    def dfs_search(self, current, remaining_types, parts_by_type, min_stats):
        if not remaining_types:
            # Check current build stat and compare
            stats = compute_total_stats(current)
            for stat, threshold in min_stats.items():
                val = stats.get(stat, 0)
                if stat == "reloadTime":
                    if val > threshold:
                        return None
                else:
                    if val < threshold:
                        return None
            return current
        
        next_type = remaining_types[0]
        for candidate in parts_by_type[next_type]:
            compatible = True
            for part in current:
                if not self.graph.has_edge(part['id'], candidate['id']):
                    compatible = False
                    break
            
            if compatible:
                result = self.dfs_search(current + [candidate], remaining_types[1:], parts_by_type,  min_stats)
                if result:
                    return result
        return None

    def generate_weapon(self):
        
        # Fetch UI Fields
        selected_class = self.class_var.get().strip()
        selected_manu = self.manu_var.get().strip().lower()
        selected_elem = self.elem_var.get().strip().lower()
        min_stats = {}
        for stat_key, var in self.stat_vars.items():
            threshold_value = var.get()
            min_stats[stat_key] = threshold_value

        self.output_box.delete("1.0", tk.END)
        
        weapon_parts = [p for p in self.parts if p.get("class") == selected_class]

        # Matching Manufacturer check
        if selected_manu:
            if self.match_var.get():
                weapon_parts = [p for p in weapon_parts if p.get("manufacturer", "").lower() == selected_manu] 
                # Discard other manufacturer part if toggled
            else:
                bodies = [p for p in weapon_parts if p.get("type") == "body" and p.get("manufacturer", "").lower() == selected_manu]
                others = [p for p in weapon_parts if p.get("type") != "body"]
                weapon_parts = bodies + others

        element_parts = []
        if selected_elem:
            element_parts = [p for p in self.parts if p.get("type") == "element" and p["id"].lower() == selected_elem]

        pool = weapon_parts + element_parts
        
        types = sorted({p.get("type") for p in pool})
        parts_by_type = {t: [p for p in pool if p.get("type") == t] for t in types}
        
        start_type = 'body' if 'body' in types else types[0]
        remaining_types = [t for t in types if t != start_type]
        for start_part in parts_by_type[start_type]:
            combo = self.dfs_search(current=[start_part], remaining_types=remaining_types, parts_by_type=parts_by_type, min_stats=min_stats)
            if combo:
                self.display_result(combo)
                return

        self.output_box.insert(tk.END, "No valid combinations found matching constraints.\n")
        self.draw_subgraph([])

    def display_result(self, combo):
        self.output_box.insert(tk.END, "Valid Combination Found!\n\n")
        self.output_box.insert(tk.END, "Parts:\n")
        for part in combo:
            self.output_box.insert(tk.END, f"- {part['type'].title()}: {part['id']}\n")
        
        stats = compute_total_stats(combo)
        self.output_box.insert(tk.END, "\nStats:\n")
        for stat, val in stats.items():
            self.output_box.insert(tk.END, f"- {stat}: {val}\n")
        
        self.draw_subgraph([p['id'] for p in combo])

if __name__ == "__main__":
    app = BLWeapGenerator()
    app.mainloop()
