import customtkinter as ctk
import sys  # Programı tamamen öldürmek için gerekli kütüphane
from Tablo import TabloFrame
from Grafik import GrafikFrame

# Ayarlar
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YAPAY ZEKA DESTEKLİ STOK SİPARİŞ SİSTEMİ")

        # --- TAM EKRAN AYARI ---
        # Program açıldığında direkt tam ekran moduna geçer.
        # Kullanıcı isterse pencere kontrolleriyle küçültebilir.
        self.after(0, lambda: self.state('zoomed'))

        # Ekranı ikiye böl (Sol: Tablo, Sağ: Grafik)
        self.grid_columnconfigure(0, weight=6)  # Sol taraf (Tablo) biraz daha geniş
        self.grid_columnconfigure(1, weight=4)  # Sağ taraf (Grafik)
        self.grid_rowconfigure(0, weight=1)

        # --- SOL TARAF: TABLO VE YAPAY ZEKA ---
        self.tablo_panel = TabloFrame(self)
        self.tablo_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # --- SAĞ TARAF: GRAFİK VE CANLI VERİ ---
        self.grafik_panel = GrafikFrame(self)
        self.grafik_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # --- KAPATMA PROTOKOLÜ ---
        # Penceredeki X tuşuna basılınca 'tamamen_kapat' fonksiyonunu çalıştır
        self.protocol("WM_DELETE_WINDOW", self.tamamen_kapat)

    def tamamen_kapat(self):
        """Programı ve arkadaki tüm threadleri (Selenium vb.) zorla kapatır."""
        self.quit()  # Arayüz döngüsünü durdur
        self.destroy()  # Pencereyi yok et
        sys.exit()  # Python işlemini tamamen öldür (Kesin çözüm)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()