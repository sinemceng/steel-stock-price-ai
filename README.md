![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python\&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-LSTM-FF6F00?logo=tensorflow\&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Random%20Forest-F7931E?logo=scikitlearn\&logoColor=white)
![Status](https://img.shields.io/badge/Status-Academic%20Project-FFD700)
![License](https://img.shields.io/badge/License-Apache%202.0-D22128?logo=apache\&logoColor=white)

# 🧠📊 Yapay Zeka Destekli Çelik Fiyat ve Stok Tahmin Sistemi

> AI-Based Steel Price & Inventory Forecasting and Financial Decision Support System  
> LSTM • Random Forest • Financial Optimization • Time Series Analysis

> “Doğru zamanda, doğru miktarda, en kârlı şekilde satın al.”

<img width="1918" height="1020" alt="image" src="https://github.com/user-attachments/assets/6401f7bc-529c-48f0-808f-cdff1f787fd5" />


### 🧠 Kullanılan Yapay Zeka Modelleri
#### 1) Fiyat Tahmin Modeli – LSTM (Long Short-Term Memory)

- Girdi: Geçmiş günlük çelik fiyatları ve teknik göstergeler

- Çıktı: Gelecek 30 günün tahmini fiyatları

- Amaç: Zaman serisi yapısını öğrenerek gelecekteki fiyat trendini tahmin etmek

- Modelin yalnızca geçmişi kopyalamasını önlemek amacıyla trend katsayısı ve rastgele gürültü faktörü içeren “drift-safe” yapı uygulanmıştır.

#### 2) Stok Tahmin Modeli – Random Forest

- Girdi: Geçmiş tüketim ve üretim verileri

- Çıktı: Gelecek 30 gün için günlük tahmini hammadde ihtiyacı

- Amaç: Doğrusal olmayan tüketim kalıplarını öğrenerek stok yetersizliği veya aşırı stok oluşumunu önlemek

#### 💰 Finansal Karar Algoritması

- Sistem, tahmin edilen gelecekteki fiyat ile bugünkü fiyatı ve faiz maliyetini karşılaştırarak net kâr/zarar hesaplaması yapar.

- Net Kar = (Hedef Fiyat × Miktar) − [(Bugünkü Fiyat × Miktar) + Faiz Kaybı]

- Faiz Kaybı, paranın zaman değeri dikkate alınarak basit faiz modeli ile hesaplanmaktadır.

- Eğer Net Kar pozitif ise sistem “Alım Uygun”, negatif ise “Bekle” uyarısı vermektedir.

#### 🛠️ Kullanılan Teknolojiler

*  Python

* TensorFlow, Keras – LSTM modeli

* Scikit-learn, Joblib – Random Forest ve veri ölçekleme

* Pandas, NumPy – Veri analizi

* Selenium – Canlı veri çekme

* CustomTkinter – Grafik arayüz (GUI)

* Matplotlib – Grafik çizimleri

#### 📂 Proje Klasör Yapısı

- Main.py → Ana uygulama dosyası

- Tablo.py → Yapay zeka ve finansal hesaplama modülü

- Grafik.py → Canlı veri çekme ve grafik modülü

- msedgedriver.exe → Selenium Edge sürücüsü

- US Midwest…csv → Geçmiş fiyat verileri

- 30_gunluk…xlsx → Stok senaryo dosyası

#### 🚀 Kurulum ve Çalıştırma

- Proje bilgisayara klonlanır.

- Gerekli Python kütüphaneleri yüklenir:
  - tensorflow, scikit-learn, pandas, numpy, customtkinter, selenium, matplotlib, openpyxl, joblib

- Model dosyalarının bulunduğu klasör yolu koda uygun şekilde ayarlanır.

- Main.py dosyası çalıştırılır.

#### 📊 Veri Seti Hakkında Bilgi

* Projede kullanılan fiyat verisi, **US Midwest bölgesine ait günlük çelik (HRC) fiyatlarından** oluşmaktadır. Bu veri seti, **Investing.com platformundan manuel olarak indirilmiştir**.
* Veri seti günlük periyottadır ve geçmiş yıllara ait fiyat hareketlerini içermektedir.
* Bu veriler, zaman serisi yapısını öğrenmesi amacıyla **LSTM modelinin eğitilmesinde** kullanılmıştır.
* Ham veriler üzerinde eksik veri temizleme, normalizasyon ve ölçekleme işlemleri uygulanmıştır.

#### 📈 Model Performansı

Bu projede modeller çalışır durumda uygulanmıştır. Sayısal performans metrikleri (RMSE, MAE, R²) ilerleyen aşamalarda detaylı olarak genişletilebilir.

#### ⚠️ Sınırlılıklar

- Model yalnızca geçmiş verilere dayalıdır ve ani ekonomik krizleri öngöremez.

- Web scraping işlemlerinde bağlantı kopmaları yaşanabilir.

- Faiz oranı sabit kabul edilmiştir.

- Enflasyon etkisi doğrudan modele dahil edilmemiştir.

###### 📜 Lisans

Bu proje Apache License 2.0 altında lisanslanmıştır.

Apache 2.0 lisansı, yazılımın akademik ve ticari amaçlarla serbestçe kullanılmasına, değiştirilmesine ve dağıtılmasına izin verir. Ancak telif hakkı bildiriminin korunması zorunludur.

Detaylı lisans metni için LICENSE dosyasına bakınız.

✅ Not: Bu proje eğitim amaçlıdır ve bir ders kapsamında geliştirilmiştir. Gerçek ticari yatırımlar için doğrudan referans alınmamalıdır.
