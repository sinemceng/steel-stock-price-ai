import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import threading
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- AYARLAR ---
CSV_PATH = r"US Midwest Domestic Hot-Rolled Coil Steel Futures Historical Data.csv"
EDGE_DRIVER_PATH = r"msedgedriver.exe"

# Borsa Açılış Saati (TR Saatiyle yaklaşık 02:00 - CME Globex)
BORSA_ACILIS_SAATI_STR = "02:00"


class GrafikFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- VERİYİ OKU ---
        try:
            self.df = pd.read_csv(CSV_PATH)
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            if self.df['Price'].dtype == object:
                self.df['Price'] = self.df['Price'].replace({',': ''}, regex=True).astype(float)
            self.df = self.df.sort_values("Date")

            # İlk referans (son fiyat)
            if not self.df.empty:
                self.son_referans_fiyat = self.df['Price'].iloc[-1]
            else:
                self.son_referans_fiyat = 0
        except Exception as e:
            print(f"Veri Okuma Hatası: {e}")
            self.df = pd.DataFrame(columns=["Date", "Price"])
            self.son_referans_fiyat = 0

        self.son_referans_zaman = pd.Timestamp.now()
        self.guncelleme_devam_ediyor = False  # Geri sayım kontrolü için

        # --- ARAYÜZ KURULUMU ---
        self.create_widgets()

    def create_widgets(self):
        # Grid: Sol(Grafik), Sağ(Panel), Alt(Uyarı)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # 1. SOL FRAME (Grafik Alanı)
        self.left_frame = ctk.CTkFrame(self, corner_radius=20)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # 2. SAĞ FRAME (Kontroller ve Bilgiler)
        self.right_frame = ctk.CTkFrame(self, corner_radius=20)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # 3. ALT FRAME (Olağandışı Hareket Uyarısı)
        self.bottom_frame = ctk.CTkFrame(self, height=120, corner_radius=20, fg_color="#C8E6FF")
        self.bottom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")

        # --- GRAFİK ---
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.locator = mdates.MonthLocator(interval=2)
        self.formatter = mdates.DateFormatter("%b %Y")

        # İlk çizim
        self.grafiği_yenile()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.left_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # --- SAĞ PANEL İÇERİĞİ ---
        self.create_right_panel()

        # --- ALT PANEL İÇERİĞİ ---
        self.create_bottom_panel()

    def create_right_panel(self):
        # --- BORSA DURUMU GÖSTERGESİ ---
        ctk.CTkLabel(self.right_frame, text="Borsa Durumu:", font=("Arial", 14)).pack(anchor="w", padx=15, pady=(15, 0))
        self.lbl_market_status = ctk.CTkLabel(self.right_frame, text="Kontrol Ediliyor...", font=("Arial", 14, "bold"))
        self.lbl_market_status.pack(anchor="w", padx=15)

        self.yerel_saat_kontrol()

        # --- FİYAT BİLGİLERİ ---
        ctk.CTkLabel(self.right_frame, text="\nSon Fiyat:", font=("Arial", 14)).pack(anchor="w", padx=15)
        self.lbl_son = ctk.CTkLabel(self.right_frame, text="---", font=("Arial", 14, "bold"))
        self.lbl_son.pack(anchor="w", padx=15)

        # AÇILIŞ SAATİNİ SABİT YAZIYORUZ
        ctk.CTkLabel(self.right_frame, text=f"\nAçılış ({BORSA_ACILIS_SAATI_STR}):", font=("Arial", 14)).pack(
            anchor="w", padx=15)
        self.lbl_acilis = ctk.CTkLabel(self.right_frame, text="---", font=("Arial", 14, "bold"))
        self.lbl_acilis.pack(anchor="w", padx=15)

        ctk.CTkLabel(self.right_frame, text="\nEn Yüksek:", font=("Arial", 14)).pack(anchor="w", padx=15)
        self.lbl_maks = ctk.CTkLabel(self.right_frame, text="---", font=("Arial", 14, "bold"))
        self.lbl_maks.pack(anchor="w", padx=15)

        ctk.CTkLabel(self.right_frame, text="\nEn Düşük:", font=("Arial", 14)).pack(anchor="w", padx=15)
        self.lbl_min = ctk.CTkLabel(self.right_frame, text="---", font=("Arial", 14, "bold"))
        self.lbl_min.pack(anchor="w", padx=15)

        # İlk hesaplamayı yap ve yazdır
        self.bilgileri_guncelle()

        # Anlık Fiyat Kısmı
        ctk.CTkLabel(self.right_frame, text="\nAnlık Fiyat (Canlı):", font=("Arial", 14)).pack(anchor="w", padx=15)
        self.anlik_label = ctk.CTkLabel(self.right_frame, text="---", font=("Arial", 16, "bold"), text_color="red")
        self.anlik_label.pack(anchor="w", padx=15)

        self.durum_label = ctk.CTkLabel(self.right_frame, text="", font=("Arial", 11), text_color="blue")
        self.durum_label.pack(anchor="w", padx=15)

        ctk.CTkButton(self.right_frame, text="Anlık Fiyatı Güncelle", command=self.buton_click).pack(pady=10, padx=15)

        # Sliderlar
        ctk.CTkLabel(self.right_frame, text="\nEşik (Yüzde Değişim):", font=("Arial", 12)).pack(anchor="w", padx=15)
        self.esik_slider = ctk.CTkSlider(self.right_frame, from_=1.0, to=10.0, number_of_steps=90,
                                         command=self.esik_slider_changed)
        self.esik_slider.set(3.5)
        self.esik_slider.pack(anchor="w", padx=15)
        self.esik_value_label = ctk.CTkLabel(self.right_frame, text="%3.5", font=("Arial", 11))
        self.esik_value_label.pack(anchor="w", padx=15)

        # --- ZAMAN SLIDER GÜNCELLEMESİ (10 SAAT, 5 DK ADIM) ---
        ctk.CTkLabel(self.right_frame, text="Zaman Aralığı (saat):", font=("Arial", 12)).pack(anchor="w", padx=15)
        # 0'dan 10 saate. Her adım 5 dk olsun istiyoruz.
        # 10 saat = 600 dakika. 5 dk adımlarla 120 adım eder.
        self.zaman_slider = ctk.CTkSlider(self.right_frame, from_=0, to=10.0, number_of_steps=120,
                                          command=self.zaman_slider_changed)
        self.zaman_slider.set(1.0)
        self.zaman_slider.pack(anchor="w", padx=15)
        self.zaman_value_label = ctk.CTkLabel(self.right_frame, text="1 sa 0 dk", font=("Arial", 11))
        self.zaman_value_label.pack(anchor="w", padx=15)

    def create_bottom_panel(self):
        ctk.CTkLabel(self.bottom_frame, text="Olağan Dışı Fiyat Hareketliliği", font=("Arial", 16, "bold"),
                     text_color="#0B3D91").pack(anchor="w", padx=20, pady=5)
        self.olagan_label = ctk.CTkLabel(self.bottom_frame, text="✔️ Olağandışı hareket tespit edilmedi.",
                                         font=("Arial", 14), text_color="black")
        self.olagan_label.pack(anchor="w", padx=20, pady=2)
        self.aciklama_label = ctk.CTkLabel(self.bottom_frame,
                                           text="(Sistem: Son 1 sa 0 dk içinde fiyatın %3.5 artış/azalış yapıp yapmadığını otomatik kontrol eder)",
                                           font=("Arial", 11), text_color="red")
        self.aciklama_label.pack(anchor="w", padx=20, pady=(0, 10))

    def yerel_saat_kontrol(self):
        simdi = datetime.now()
        gun = simdi.weekday()
        if gun == 5 or (gun == 6 and simdi.hour < 23):
            self.lbl_market_status.configure(text="Piyasa Kapalı (Haftasonu)", text_color="red")
        else:
            self.lbl_market_status.configure(text="Piyasa Açık", text_color="green")

    def bilgileri_guncelle(self):
        son_saat_str = ""

        if not self.df.empty:
            son_veri_row = self.df.iloc[-1]
            son_tarih = son_veri_row['Date'].date()
            bugunun_verisi = self.df[self.df['Date'].dt.date == son_tarih]

            if not bugunun_verisi.empty:
                son = bugunun_verisi['Price'].iloc[-1]
                son_zaman = bugunun_verisi['Date'].iloc[-1]
                son_saat_str = son_zaman.strftime("%H:%M")

                # --- AÇILIŞ FİYATI MANTIĞI (ÖZEL SAAT: 02:00) ---
                # Hedef saat: Bugünün tarihi + 02:00
                hedef_acilis_zamani = pd.Timestamp(
                    datetime.combine(son_tarih, datetime.strptime(BORSA_ACILIS_SAATI_STR, "%H:%M").time()))

                # Bu zamandan sonraki verilere bak
                acilis_sonrasi_veri = bugunun_verisi[bugunun_verisi['Date'] >= hedef_acilis_zamani]

                if not acilis_sonrasi_veri.empty:
                    # 02:00 sonrası ilk veri
                    acilis = acilis_sonrasi_veri['Price'].iloc[0]
                else:
                    # Eğer 02:00 sonrası veri yoksa en eski veriyi al (henüz piyasa 02:00'ye gelmediyse)
                    acilis = bugunun_verisi['Price'].iloc[0]

                maks = bugunun_verisi['Price'].max()
                min_p = bugunun_verisi['Price'].min()
            else:
                son = self.df['Price'].iloc[-1]
                son_saat_str = self.df['Date'].iloc[-1].strftime("%H:%M")
                acilis = maks = min_p = son
        else:
            son = acilis = maks = min_p = 0

        self.lbl_son.configure(text=f"${son}  ({son_saat_str})")
        self.lbl_acilis.configure(text=f"${acilis}")
        self.lbl_maks.configure(text=f"${maks}")
        self.lbl_min.configure(text=f"${min_p}")

    def grafiği_yenile(self):
        self.ax.clear()
        self.ax.plot(self.df["Date"], self.df["Price"], linewidth=2)
        self.ax.set_title("US Midwest Domestic Hot-Rolled Coil Steel Futures")
        self.ax.set_ylabel("Price")
        self.ax.xaxis.set_major_locator(self.locator)
        self.ax.xaxis.set_major_formatter(self.formatter)
        plt.setp(self.ax.get_xticklabels(), rotation=30)
        self.ax.grid(True, linestyle="--", alpha=0.5)
        if hasattr(self, 'canvas'):
            self.canvas.draw()

    def esik_slider_changed(self, value):
        self.esik_value_label.configure(text=f"%{value:.1f}")
        self.guncelle_aciklama()

    def zaman_slider_changed(self, value):
        saat = int(value)
        # Dakikayı 5'in katlarına yuvarla
        dakika_ham = int((value - saat) * 60)
        dakika = round(dakika_ham / 5) * 5
        if dakika == 60:
            saat += 1
            dakika = 0

        txt = f"{saat} sa {dakika} dk"
        self.zaman_value_label.configure(text=txt)
        self.guncelle_aciklama()

    def guncelle_aciklama(self):
        saat_text = self.zaman_value_label.cget("text")
        esik_yuzde = self.esik_slider.get()
        self.aciklama_label.configure(
            text=f"(Sistem: Son {saat_text} içinde fiyatın %{esik_yuzde:.1f} artış/azalış yapıp yapmadığını otomatik kontrol eder)"
        )

    def buton_click(self):
        if not self.guncelleme_devam_ediyor:
            self.guncelleme_devam_ediyor = True
            threading.Thread(target=self.geri_sayim_animasyonu, daemon=True).start()
            threading.Thread(target=self.fiyat_guncelle, daemon=True).start()

    def geri_sayim_animasyonu(self):
        """Tahmini süre sayacı"""
        tahmini_sure = 15  # saniye
        while self.guncelleme_devam_ediyor and tahmini_sure > 0:
            self.durum_label.configure(text=f"Veri Çekiliyor... ({tahmini_sure} sn)")
            time.sleep(1)
            tahmini_sure -= 1

        if self.guncelleme_devam_ediyor:
            self.durum_label.configure(text="Sonuç bekleniyor...")

    def fiyat_guncelle(self):
        sonuc = self.anlik_fiyat_al()
        self.guncelleme_devam_ediyor = False
        self.after(0, lambda: self.sonuc_islet(sonuc))

    def sonuc_islet(self, sonuc):
        fiyat, borsa_durumu = sonuc

        if fiyat is None:
            self.anlik_label.configure(text="Hata")
            self.durum_label.configure(text="Fiyat alınamadı")
        else:
            self.anlik_label.configure(text=f"${fiyat}")
            self.durum_label.configure(text="")

            if borsa_durumu and "Bilinmiyor" not in borsa_durumu:
                renk = "green"
                if "Closed" in borsa_durumu or "Kapalı" in borsa_durumu:
                    renk = "red"
                self.lbl_market_status.configure(text=borsa_durumu, text_color=renk)
            else:
                self.yerel_saat_kontrol()

            yeni_satir = {"Date": pd.Timestamp.now(), "Price": fiyat}
            for col in self.df.columns:
                if col not in yeni_satir:
                    yeni_satir[col] = None

            self.df.loc[len(self.df)] = yeni_satir

            self.grafiği_yenile()
            self.bilgileri_guncelle()
            self.olagan_disi_kontrol(fiyat)

    def olagan_disi_kontrol(self, yeni_fiyat):
        simdi = pd.Timestamp.now()
        gecen_saat = (simdi - self.son_referans_zaman).total_seconds() / 3600
        zaman_esigi = self.zaman_slider.get()
        esik_yuzde = self.esik_slider.get()

        if gecen_saat <= zaman_esigi:
            degisim = ((yeni_fiyat - self.son_referans_fiyat) / self.son_referans_fiyat) * 100
            if abs(degisim) >= esik_yuzde:
                if degisim > 0:
                    self.olagan_label.configure(text=f"⚠️ Seçilen aralıkta fiyat %{degisim:.2f} ARTTI!",
                                                text_color="green")
                else:
                    self.olagan_label.configure(text=f"⚠️ Seçilen aralıkta fiyat %{abs(degisim):.2f} AZALDI!",
                                                text_color="red")
            else:
                self.olagan_label.configure(text="✔️ Olağandışı hareket tespit edilmedi.", text_color="black")
        else:
            self.son_referans_fiyat = yeni_fiyat
            self.son_referans_zaman = simdi
            self.olagan_label.configure(text="✔️ Referans fiyat güncellendi (Süre doldu).", text_color="black")

    # --- SELENIUM KISMI ---
    def anlik_fiyat_al(self):
        driver = None
        fiyat = None
        borsa_durumu_text = "Bilinmiyor"

        try:
            edge_options = Options()
            edge_options.add_argument("--headless")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--guest")
            edge_options.add_argument("--disable-features=msEdgeIdentity,msEdgeIdentityConsistency")
            edge_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            service = Service(EDGE_DRIVER_PATH)
            driver = webdriver.Edge(service=service, options=edge_options)

            wait = WebDriverWait(driver, 25)
            driver.get("https://www.investing.com/commodities/us-steel-coil-futures")

            try:
                accept = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                accept.click()
            except:
                pass

            try:
                status_selectors = [
                    "//div[contains(@class, 'instrument-metadata_status')]",
                    "//div[contains(@class, 'trading-hours_value')]",
                    "//span[contains(@class, 'trading-state')]",
                    "//*[@data-test='instrument-status']",
                    "//div[contains(@class, 'market-info')]/div[1]",
                    "//time[@data-test='instrument-metadata-time']"
                ]

                for xp in status_selectors:
                    try:
                        status_el = driver.find_element(By.XPATH, xp)
                        text = status_el.text.strip()
                        if text:
                            borsa_durumu_text = text
                            break
                    except:
                        continue
            except:
                pass

            price_selectors = [
                "//span[@data-test='instrument-price-last']",
                "//div[@data-test='instrument-price-last']",
                "//span[contains(@class,'last-price')]",
                "//div[contains(@class,'text') and contains(@class,'xl')]"
            ]

            for xp in price_selectors:
                try:
                    el = wait.until(EC.visibility_of_element_located((By.XPATH, xp)))
                    fiyat_text = el.text.strip()
                    if fiyat_text:
                        fiyat_text = fiyat_text.replace(",", "")
                        fiyat = float(fiyat_text)
                        break
                except:
                    continue

            return (fiyat, borsa_durumu_text)

        except Exception as e:
            print(f"Selenium Hatası: {e}")
            return (None, None)
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass