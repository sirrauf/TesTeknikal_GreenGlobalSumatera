import re
import sys
import subprocess
from datetime import datetime


REQUIRED = ["ezdxf", "svgwrite"]
for pkg in REQUIRED:
    try:
        __import__(pkg)
    except ImportError:
        print(f"Package '{pkg}' belum ditemukan. Menginstall {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import ezdxf
import svgwrite


HAS_TRIMESH = True
try:
    import numpy as np
    import trimesh
except Exception:
    HAS_TRIMESH = False


def to_number(s):
    
    try:
        return float(s)
    except Exception:
        return None


class CADItem:
    
    def __init__(self, kind, **kwargs):
        self.kind = kind  # 'seat', 'leg', 'room', 'door', 'window', 'rect', 'circle', ...
        self.props = kwargs


class TextToCADConverter:
    
    def __init__(self):
        self.items = []  

  
    def parse(self, description: str):
        desc = description.lower().strip()
        
        desc = desc.replace("×", "x")
        desc = desc.replace("X", "x")

        
        if "kursi" in desc or "chair" in desc:
            self._parse_chair(desc)
       
        elif "ruangan" in desc or "room" in desc:
            self._parse_room(desc)
        else:
            
            self._parse_basic_shapes(desc)

    def _parse_chair(self, desc: str):
        
        seat_w = 40.0
        seat_d = 40.0
        seat_h = 45.0
        legs = 4

       
        m = re.search(r'dudukan.*?(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(cm|mm|m)?', desc)
        if m:
            a = float(m.group(1))
            b = float(m.group(2))
            unit = m.group(3)
            if unit == "m":
                a *= 100.0
                b *= 100.0
            elif unit == "mm":
                a /= 10.0
                b /= 10.0
            seat_w, seat_d = a, b
        else:
            
            m2 = re.search(r'dudukan.*?(\d+(?:\.\d+)?)\s*(cm|mm|m)?', desc)
            if m2:
                val = float(m2.group(1))
                unit = m2.group(2)
                if unit == "m":
                    val *= 100.0
                elif unit == "mm":
                    val /= 10.0
                seat_w = seat_d = val

        
        mh = re.search(r'tinggi.*?(\d+(?:\.\d+)?)\s*(cm|mm|m)?', desc)
        if mh:
            v = float(mh.group(1))
            u = mh.group(2)
            if u == "m":
                v *= 100.0
            elif u == "mm":
                v /= 10.0
            seat_h = v

        
        mleg = re.search(r'(\d+)\s*kaki', desc)
        if mleg:
            legs = int(mleg.group(1))

        
        seat_x = 0.0
        seat_y = 0.0
        self.items.append(CADItem("seat", x=seat_x, y=seat_y, width=seat_w, depth=seat_d, height=seat_h))

        
        leg_radius = max(min(seat_w, seat_d) * 0.05, 0.5)  
        leg_pos = []
       
        if legs == 1:
            leg_pos = [(seat_x + seat_w / 2, seat_y + seat_d / 2)]
        elif legs == 2:
            leg_pos = [(seat_x + 0.15 * seat_w, seat_y + seat_d / 2),
                       (seat_x + 0.85 * seat_w, seat_y + seat_d / 2)]
        elif legs == 3:
            leg_pos = [(seat_x + 0.1 * seat_w, seat_y + 0.9 * seat_d),
                       (seat_x + 0.9 * seat_w, seat_y + 0.9 * seat_d),
                       (seat_x + 0.5 * seat_w, seat_y + 0.1 * seat_d)]
        else:
            
            leg_pos = [
                (seat_x + 0.1 * seat_w, seat_y + 0.1 * seat_d),
                (seat_x + 0.9 * seat_w, seat_y + 0.1 * seat_d),
                (seat_x + 0.1 * seat_w, seat_y + 0.9 * seat_d),
                (seat_x + 0.9 * seat_w, seat_y + 0.9 * seat_d),
            ]
            if legs > 4:
                leg_pos.append((seat_x + 0.5 * seat_w, seat_y + 0.5 * seat_d))

        for lx, ly in leg_pos[:legs]:
            self.items.append(CADItem("leg", cx=lx, cy=ly, radius=leg_radius, height=seat_h))

    def _parse_room(self, desc: str):
        
        room_w = 400.0
        room_d = 500.0

       
        m = re.search(r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)(?:\s*(m|meter|cm|mm))?', desc)
        if m:
            a = float(m.group(1))
            b = float(m.group(2))
            unit = m.group(3)
            if unit and unit.startswith("m"):
                a *= 100.0
                b *= 100.0
            elif unit == "cm" or (unit is None and "meter" not in desc and "cm" in desc):
                
                a = a if unit == "cm" else a
           
            room_w, room_d = a * (100.0 if unit and unit.startswith("m") else 1.0), b * (100.0 if unit and unit.startswith("m") else 1.0)

       
        if "meter" in desc and "x" in desc and not m:
            m2 = re.search(r'(\d+(?:\.\d+)?)\s*m', desc)
            if m2:
                
                val = float(m2.group(1)) * 100.0
                room_w = room_d = val

        
        self.items.append(CADItem("room", x=0.0, y=0.0, width=room_w, depth=room_d, height=300.0))

        
        sides_map = {"barat": "west", "timur": "east", "utara": "north", "selatan": "south"}
        
        for kind in ["pintu", "jendela"]:
            for m2 in re.finditer(rf'(\d+)?\s*{kind}.*?(barat|timur|utara|selatan)?', desc):
                count_raw = m2.group(1)
                side_raw = m2.group(2)
                count = int(count_raw) if count_raw else 1
                side = sides_map.get(side_raw, None) if side_raw else None
                for _ in range(count):
                    
                    if kind == "pintu":
                        w = 90.0  # cm
                        h = 210.0
                        self.items.append(CADItem("door", side=side or "south", width=w, height=h))
                    else:
                        w = 120.0
                        h = 120.0
                        self.items.append(CADItem("window", side=side or "north", width=w, height=h))

    def _parse_basic_shapes(self, desc: str):
        
        if "kotak" in desc or "persegi" in desc:
            m = re.search(r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)(?:\s*(cm|mm|m))?', desc)
            if m:
                a = float(m.group(1))
                b = float(m.group(2))
                unit = m.group(3)
                if unit == "m":
                    a *= 100.0
                    b *= 100.0
                elif unit == "mm":
                    a /= 10.0
                    b /= 10.0
                self.items.append(CADItem("rect", x=0.0, y=0.0, width=a, depth=b, height=30.0))
                return
        if "lingkaran" in desc or "circle" in desc:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(cm|mm|m)?', desc)
            if m:
                r = float(m.group(1))
                u = m.group(2)
                if u == "m":
                    r *= 100.0
                elif u == "mm":
                    r /= 10.0
                self.items.append(CADItem("circle", cx=r, cy=r, radius=r, height=30.0))
                return

        
        self.items.append(CADItem("rect", x=0.0, y=0.0, width=100.0, depth=50.0, height=30.0))

    def render_dxf(self, filename: str):
        doc = ezdxf.new("R2010")
        msp = doc.modelspace()

       
        msp.add_text("TAMPAK ATAS", dxfattribs={"height": 5, "insert": (0, -10)})
        msp.add_text("TAMPAK DEPAN", dxfattribs={"height": 5, "insert": (0, 300)})

        
        for item in self.items:
            if item.kind == "seat" or item.kind == "rect":
                x = item.props.get("x", 0.0)
                y = item.props.get("y", 0.0)
                w = item.props.get("width")
                d = item.props.get("depth")
                pts = [(x, y), (x + w, y), (x + w, y + d), (x, y + d), (x, y)]
                msp.add_lwpolyline(pts)
            elif item.kind == "circle":
                cx = item.props.get("cx", 0.0)
                cy = item.props.get("cy", 0.0)
                r = item.props.get("radius", 1.0)
                msp.add_circle((cx, cy), r)
            elif item.kind == "leg":
                cx = item.props.get("cx")
                cy = item.props.get("cy")
                r = item.props.get("radius", 1.0)
                
                msp.add_circle((cx, cy), r)
            elif item.kind == "room":
                x = item.props.get("x", 0.0)
                y = item.props.get("y", 0.0)
                w = item.props.get("width", 400.0)
                d = item.props.get("depth", 500.0)
                pts = [(x, y), (x + w, y), (x + w, y + d), (x, y + d), (x, y)]
                msp.add_lwpolyline(pts)
            elif item.kind in ("door", "window"):
                
                side = item.props.get("side", "south")
                w = item.props.get("width", 90.0)
                
                room = next((it for it in self.items if it.kind == "room"), None)
                if room:
                    rx = room.props["x"]
                    ry = room.props["y"]
                    rw = room.props["width"]
                    rd = room.props["depth"]
                    if side == "north":
                        
                        x0 = rx + (rw - w) / 2
                        y0 = ry
                        pts = [(x0, y0 - 0.5), (x0 + w, y0 - 0.5), (x0 + w, y0 + 0.5), (x0, y0 + 0.5), (x0, y0)]
                        msp.add_lwpolyline(pts)
                    elif side == "south":
                        x0 = rx + (rw - w) / 2
                        y0 = ry + rd
                        pts = [(x0, y0 - 0.5), (x0 + w, y0 - 0.5), (x0 + w, y0 + 0.5), (x0, y0 + 0.5), (x0, y0)]
                        msp.add_lwpolyline(pts)
                    elif side == "west":
                        x0 = rx
                        y0 = ry + (rd - w) / 2
                        pts = [(x0 - 0.5, y0), (x0 + 0.5, y0), (x0 + 0.5, y0 + w), (x0 - 0.5, y0 + w), (x0, y0)]
                        msp.add_lwpolyline(pts)
                    elif side == "east":
                        x0 = rx + rw
                        y0 = ry + (rd - w) / 2
                        pts = [(x0 - 0.5, y0), (x0 + 0.5, y0), (x0 + 0.5, y0 + w), (x0 - 0.5, y0 + w), (x0, y0)]
                        msp.add_lwpolyline(pts)

        
        y_offset = 320
        for item in self.items:
            if item.kind == "seat":
                
                x = item.props.get("x", 0.0)
                w = item.props.get("width")
                h = item.props.get("height")
          
                pts = [(x, y_offset), (x + w, y_offset), (x + w, y_offset + 5), (x, y_offset + 5), (x, y_offset)]
                msp.add_lwpolyline(pts)
               
                for leg in [it for it in self.items if it.kind == "leg"]:
                    cx = leg.props.get("cx")
                    r = leg.props.get("radius", 1.0)
                    
                    lx = cx - r
                    ly = y_offset + 5
                    lh = leg.props.get("height", h)
                    pts = [(lx, ly), (lx + r * 2, ly), (lx + r * 2, ly + lh), (lx, ly + lh), (lx, ly)]
                    msp.add_lwpolyline(pts)
            elif item.kind == "rect":
                x = item.props.get("x", 0.0)
                w = item.props.get("width", 0.0)
                h = item.props.get("height", 30.0)
                pts = [(x, y_offset), (x + w, y_offset), (x + w, y_offset + h), (x, y_offset + h), (x, y_offset)]
                msp.add_lwpolyline(pts)
            elif item.kind == "room":
                
                x = item.props.get("x", 0.0)
                w = item.props.get("width", 0.0)
                h = item.props.get("height", 300.0)
                pts = [(x, y_offset), (x + w, y_offset), (x + w, y_offset + h), (x, y_offset + h), (x, y_offset)]
                msp.add_lwpolyline(pts)
                
                for iw in [it for it in self.items if it.kind in ("window", "door")]:
                    ww = iw.props.get("width", 90.0)
                    wh = iw.props.get("height", 120.0) if iw.kind == "window" else iw.props.get("height", 210.0)
                    
                    cx = x + w / 2
                    lx = cx - ww / 2
                    ly = y_offset + 50  
                    pts = [(lx, ly), (lx + ww, ly), (lx + ww, ly + wh), (lx, ly + wh), (lx, ly)]
                    msp.add_lwpolyline(pts)

        
        doc.saveas(filename)
        return filename

    def render_svg(self, filename: str):
        
        minx, miny, maxx, maxy = 0, 0, 800, 600
        
        all_x = []
        all_y = []
        for it in self.items:
            if it.kind in ("seat", "rect", "room"):
                x = it.props.get("x", 0.0)
                y = it.props.get("y", 0.0)
                w = it.props.get("width", 0.0)
                d = it.props.get("depth", 0.0)
                all_x.extend([x, x + w])
                all_y.extend([y, y + d])
            elif it.kind == "circle":
                cx = it.props.get("cx", 0.0)
                cy = it.props.get("cy", 0.0)
                r = it.props.get("radius", 0.0)
                all_x.extend([cx - r, cx + r])
                all_y.extend([cy - r, cy + r])
            elif it.kind == "leg":
                cx = it.props.get("cx", 0.0)
                cy = it.props.get("cy", 0.0)
                all_x.append(cx)
                all_y.append(cy)
        if all_x and all_y:
            minx, maxx = min(all_x) - 20, max(all_x) + 20
            miny, maxy = min(all_y) - 20, max(all_y) + 20

        width = int(max(800, maxx - minx + 200))
        height = int(max(600, maxy - miny + 600))
        dwg = svgwrite.Drawing(filename, size=(f"{width}px", f"{height}px"))

        # top view group
        top_group = dwg.add(dwg.g(id="top_view", transform=f"translate({50 - minx}, {50 - miny})"))
        top_group.add(dwg.text("TAMPAK ATAS", insert=(0, -10), font_size="14px", font_weight="bold"))

        for it in self.items:
            if it.kind in ("seat", "rect", "room"):
                x = it.props.get("x", 0.0)
                y = it.props.get("y", 0.0)
                w = it.props.get("width", 0.0)
                d = it.props.get("depth", 0.0)
                top_group.add(dwg.rect(insert=(x, y), size=(w, d), fill="none", stroke="black", stroke_width=2))
            elif it.kind == "circle":
                cx = it.props.get("cx", 0.0)
                cy = it.props.get("cy", 0.0)
                r = it.props.get("radius", 0.0)
                top_group.add(dwg.circle(center=(cx, cy), r=r, fill="none", stroke="black", stroke_width=2))
            elif it.kind == "leg":
                cx = it.props.get("cx", 0.0)
                cy = it.props.get("cy", 0.0)
                r = it.props.get("radius", 1.0)
                top_group.add(dwg.circle(center=(cx, cy), r=r, fill="black"))

      
        front_y_offset = maxy - miny + 120
        front_group = dwg.add(dwg.g(id="front_view", transform=f"translate({50 - minx}, {front_y_offset})"))
        front_group.add(dwg.text("TAMPAK DEPAN", insert=(0, -10), font_size="14px", font_weight="bold"))

        for it in self.items:
            if it.kind == "seat":
                x = it.props.get("x", 0.0)
                w = it.props.get("width", 0.0)
                h = it.props.get("height", 45.0)
                
                front_group.add(dwg.rect(insert=(x, 0), size=(w, 5), fill="none", stroke="black", stroke_width=2))
                
                for leg in [l for l in self.items if l.kind == "leg"]:
                    cx = leg.props.get("cx")
                    r = leg.props.get("radius", 1.0)
                    lx = cx - r
                    ly = 5
                    lh = leg.props.get("height", h)
                    front_group.add(dwg.rect(insert=(lx, ly), size=(r * 2, lh), fill="none", stroke="black", stroke_width=2))
            elif it.kind == "rect":
                x = it.props.get("x", 0.0)
                w = it.props.get("width", 0.0)
                h = it.props.get("height", 30.0)
                front_group.add(dwg.rect(insert=(x, 0), size=(w, h), fill="none", stroke="black", stroke_width=2))
            elif it.kind == "room":
                x = it.props.get("x", 0.0)
                w = it.props.get("width", 400.0)
                h = it.props.get("height", 300.0)
                front_group.add(dwg.rect(insert=(x, 0), size=(w, h), fill="none", stroke="black", stroke_width=2))
              
                for iw in [it for it in self.items if it.kind in ("window", "door")]:
                    ww = iw.props.get("width", 90.0)
                    wh = iw.props.get("height", 120.0) if iw.kind == "window" else iw.props.get("height", 210.0)
                    cx = x + w / 2
                    lx = cx - ww / 2
                    ly = 50
                    front_group.add(dwg.rect(insert=(lx, ly), size=(ww, wh), fill="none", stroke="black", stroke_width=2))

        dwg.save()
        return filename
    
    def export_obj_extrude(self, filename: str):
        if not HAS_TRIMESH:
            print("trimesh/numpy tidak tersedia — melewatkan ekspor 3D.")
            return None

        meshes = []
        for it in self.items:
            if it.kind in ("seat", "rect", "room"):
                x = it.props.get("x", 0.0)
                y = it.props.get("y", 0.0)
                w = it.props.get("width", 0.0)
                d = it.props.get("depth", 0.0)
                h = it.props.get("height", 10.0)

                # buat box 3D (ekstrusi persegi panjang)
                mesh = trimesh.creation.box(extents=(w, d, h))
                mesh.apply_translation((x + w / 2, y + d / 2, h / 2))
                meshes.append(mesh)

            elif it.kind == "circle":
                cx = it.props.get("cx", 0.0)
                cy = it.props.get("cy", 0.0)
                r = it.props.get("radius", 1.0)
                h = it.props.get("height", 10.0)

                # buat silinder 3D (ekstrusi lingkaran)
                mesh = trimesh.creation.cylinder(radius=r, height=h, sections=32)
                mesh.apply_translation((cx, cy, h / 2))
                meshes.append(mesh)

        if not meshes:
            print("Tidak ada mesh untuk diekspor.")
            return None

        scene = trimesh.util.concatenate(meshes)
        scene.export(filename)
        return filename


def main():
    print("========================================================================\n")

    namaprogram = "Test Teknikal PT Green Global Sumatera\n"
    devby = "Developed by Ananda Rauf Maududi\n"
    devdate = "Tanggal Test: 24 September 2025\n"

    print(namaprogram)
    print(devby)
    print(devdate)
    print("========================================================================\n")

    print("Contoh input yang dapat diproses:")
    print("- 'Kursi dengan 4 kaki, dudukan persegi 40x40 cm, tinggi 45 cm'")
    print("- 'Ruangan ukuran 4x5 meter, dengan 1 pintu di sisi barat dan 1 jendela di sisi utara'")
    print("- 'Kotak 100x50' atau 'Lingkaran diameter 80'\n")

    input_deskripsi_sketsa = input("Masukan deskripsi sketsa anda: ")

    converter = TextToCADConverter()
    converter.parse(input_deskripsi_sketsa)

   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dxf_filename = f"output_{timestamp}.dxf"
    svg_filename = f"output_{timestamp}.svg"

    try:
        converter.render_dxf(dxf_filename)
        print(f"DXF berhasil dibuat: {dxf_filename}")
    except Exception as e:
        print("Gagal membuat DXF:", e)

    try:
        converter.render_svg(svg_filename)
        print(f"SVG berhasil dibuat: {svg_filename}")
    except Exception as e:
        print("Gagal membuat SVG:", e)


    if HAS_TRIMESH:
        obj_filename = f"output_{timestamp}.obj"
        try:
            converter.export_obj_extrude(obj_filename)
            print(f"OBJ ekstrusi (3D) dibuat: {obj_filename}")
        except Exception as e:
            print("Gagal membuat OBJ ekstrusi:", e)
    else:
        print("Trimesh tidak tersedia — lewati ekspor 3D (instal 'trimesh' dan 'numpy' jika ingin).")

 
    if converter.items:
        print("\nBenda yang terdeteksi:")
        for i, it in enumerate(converter.items, 1):
            print(f"{i}. type={it.kind}, props={it.props}")

    print("\nSelesai.")


if __name__ == "__main__":
    main()
