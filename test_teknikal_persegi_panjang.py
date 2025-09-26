import ezdxf
import matplotlib.pyplot as plt


print("========================================================================\n")

namaprogram = "Test Teknikal PT Green Global Sumatera\n"
devby = "Developed by Ananda Rauf Maududi\n"
devdate = "Tanggal Test: 23 September 2025\n"

print(namaprogram)
print(devby)
print(devdate)
print("========================================================================\n")



dimension_length = int(input("Masukan ukuran dimension length: "))
dimension_width = int(input("Masukan ukuran dimension width: "))



doc = ezdxf.new(dxfversion="R2010")
msp = doc.modelspace()


points = [
    (0, 0),
    (dimension_length, 0),
    (dimension_length, dimension_width),
    (0, dimension_width),
    (0, 0)  
]

msp.add_lwpolyline(points, close=True)

dxf_filename = "output_persegi_panjang.dxf"
doc.saveas(dxf_filename)
print(f"File DXF berhasil dibuat: {dxf_filename}")


x_coords = [p[0] for p in points]
y_coords = [p[1] for p in points]

plt.figure(figsize=(6, 6))
plt.plot(x_coords, y_coords, 'b-', linewidth=2)
plt.fill(x_coords, y_coords, alpha=0.2, color='skyblue')
plt.title(f"Preview Persegi Panjang ({dimension_length} x {dimension_width})")
plt.axis('equal')
plt.grid(True)

png_filename = "output_persegipanjang.png"
plt.savefig(png_filename, dpi=150)
plt.close()
print(f"File PNG berhasil dibuat: {png_filename}")
