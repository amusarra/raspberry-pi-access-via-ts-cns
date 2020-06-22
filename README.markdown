# Raspberry Pi - Un esempio di applicazione della TS-CNS

Questo progetto nasce dalla composizione dei seguenti "pezzi di ferro".

1. Raspberry Pi 3 Model B+
2. Display LCD 16x2
3. Modulo quattro relè
4. Key Pad 16 caratteri (4x4)
5. Lettore Smart Card Bit4id

Recentemente ho utilizzato il display LCD e il modulo da quattro relè nel
progetto [Un primo maggio 2020 a base di Raspberry Pi, Bot Telegram, Display LCD e Relè](https://bit.ly/UnPrimoMaggio2020ABaseDiRaspberryPiBotTelegramDisplayLCDRele)
che vi invito a leggere.

Quelli che vedete nella figura a seguire sono i componenti utilizzati (a meno della tastiera).

![Componenti del progetto](./docs/images/pezzi_di_ferro_progetto.jpeg)

L’idea alla base della “ricetta” è quella di realizzare un sistema di sicurezza 
tale per cui è possibile attivare una serie di relè solo dopo che l'utilizzare del sistema
esegua con successo l'autenticazione tramite la propria TS-CNS (Tessera Sanitaria - 
Carta Nazionale dei Servizi). Sul sito dell'[Agenzia per l'Italia digitale (AgID)](https://www.agid.gov.it/it/piattaforme/carta-nazionale-servizi)
sono pubblicate tutte le informazioni di dettaglio sulla **Carta Nazionale dei Servizi**.

Sul mio canale YouTube Antonio Musarra's Blog, è disponibile un breve video che mostra
quello che si può realizzare con un Raspberry Pi, un lettore di Smart Card, un Key Pad 4x4, 
un modulo da quattro relè, un display LCD 16x2 e la propria TS-CNS (Tessera Sanitaria - 
Carta Nazionale dei Servizi).



[![Un sistema di accesso basato sulla Smart Card TS-CNS e Raspberry Pi](https://img.youtube.com/vi/_lOdD6tjSDo/0.jpg)](https://www.youtube.com/watch?v=_lOdD6tjSDo)

## 1. Schema elettrico della soluzione
Dando per scontato che abbiate tutto il materiale hardware a vostra disposizione (vedi capitolo 2. Requisiti), possiamo 
disporre tutti collegamenti tra i vari componenti hardware che compongono la soluzione, così come indicato dallo schema 
elettrico mostrato a seguire.

Al fine di facilitare i collegamenti ho indicato nelle note quali sono i pin (BCM) che ogni componente 
utilizzerà. Per quanto riguarda il layout del connettore J8 del Raspberry PI, fate riferimento alla 
documentazione ufficiale su [GPIO (general-purpose input/output)](https://www.raspberrypi.org/documentation/usage/gpio/).



![Schema elettrico della soluzione](./docs/images/fritzing_schema_soluzione.png)

## 2. Requisiti
Per raggiungere l'obiettivo abbiamo bisogno di raccogliere un pochino di materiale, dobbiamo fare una sorta di lista 
della spesa, sia in termini hardware, sia in termini software. Partiamo dal basso, con la lista dell’hardware.

1. [**Raspberry Pi**](https://amzn.to/2KX1ybU): ho utilizzato la versione 3 Model B+ 
che sarà il riferimento di questo articolo. Per coloro che hanno a disposizione 
il [Raspberry Pi 2](https://amzn.to/35rsKJf) o il [Raspberry Pi 4](https://amzn.to/35vh4FE), 
non dovrebbe essere un problema.
2. [**Modulo Relè**](https://amzn.to/3b2zpLc): ho utilizzato il modello Elegoo 4 Channel 
DC 5V Modulo Relay con Accoppiatore Ottico. A quanto pare è difficile trovare questo modello, 
al suo posto, anche su Amazon, è stato sostituito con il modulo da otto. In ogni caso per 
questo esperimento va benissimo anche il modulo con due o al peggio un solo Relè.
3. [**Display LCD**](https://amzn.to/2KRkiK5): ho utilizzato un display LCD I2C 1602 16X2.
4. [**Key Pad 16 caratteri (4x4)**](https://amzn.to/2V5UgIg): ho scelto questo tastierino
con lettere e caratteri "speciali" per un motivo che vedremo dopo.
5. [**Breadboard**](https://amzn.to/2SsrX5t), [**GPIO Extender**](https://amzn.to/3fd8eRa), [**Cavi Maschio a Femmina Dupont**](https://amzn.to/3bYFo5b) e [**Cavi Maschio a Maschio Dupont**](https://amzn.to/3drg1c7) utilizzati per 
realizzare i collegamenti tra il Raspberry Pi, il modulo LCD, il modulo Relè e il Key Pad.

Tutti i componenti hardware possono essere acquisitati separatamente, però, se l’argomento vi appassiona, consiglio 
l’acquisito dello Starter Kit Freenove RFID per Raspberry Pi. All’interno del kit sono inclusi gli ultimi elementi 
della nostra lista, oltre ad altri numerosi componenti.

Per quanto riguarda il software abbiamo bisogno di:

1. [**Raspbian OS**](https://www.raspberrypi.org/downloads/raspbian/): a meno di applicazioni 
particolari, questo sistema operativo basato su Debian è ottimizzato per la piattaforma Raspberry Pi. 
L’ultima versione disponibile è **Raspbian Buster**. Sul mio Raspberry Pi 3 B+ ho installato 
quest’ultima release. Per maggiori informazioni sull’installazione del sistema operativo, fare 
riferimento alla guida ufficiale ([Installing operating system images](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)). Questo sarà comunque il 
sistema operativo di riferimento.
2. **Python 3.x**: sul mio Raspberry Pi ho installato sia la versione 2.7 (quella di default) 
sia la versione 3.7, quest’ultima disponibile OOTB con l’ultima versione di Raspbian OS.
3. [**pad4pi**](https://pypi.org/project/pad4pi/): modulo Python per la gestione del Key Pad.
4. **Moduli software display LCD**: moduli Python per utilizzare il display LCD. Utilizzeremo 
i moduli scritti da [Freenove](http://www.freenove.com/) e reperibili dal loro repository [GitHub](https://github.com/Freenove/Freenove_Ultimate_Starter_Kit_for_Raspberry_Pi).
5. **PC/SC Middleware**: Middleware per la gestione e comunicazione per le Smart Card e Smart
Card Reader.
6. [**OpenSC**](https://github.com/OpenSC/OpenSC/wiki): OpenSC fornisce una serie di librerie 
e utilità per lavorare con le smart card. Il suo focus principale è sulle schede che supportano 
le operazioni crittografiche e ne facilitano l'uso in applicazioni di sicurezza come 
l'autenticazione, la crittografia della posta e le firme digitali. OpenSC implementa le API 
standard su smart card, ad es. API PKCS#11, Minidriver per smart card di Windows e macOS 
CryptoTokenKit.


Possiamo verificare che il software attualmente installato sia conforme ai requisiti accedendo 
alla console del Raspberry Pi ed eseguendo i comandi a seguire.

```bash
# Verifica della Release del Sistema Operativo 
$ cat /etc/os-release
 
# Verifica della Release del Kernel
$ uname -a
```

A seguire è mostrato l’output dei comandi precedenti eseguiti sul mio Raspberry Pi.

```bash
# Output del comando cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 10 (buster)"
NAME="Raspbian GNU/Linux"
VERSION_ID="10"
VERSION="10 (buster)"
VERSION_CODENAME=buster
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"
 
# Output del comando uname -a
Linux amusarra-rpi 4.19.97-v7+ #1294 SMP Thu Jan 30 13:15:58 GMT 2020 armv7l GNU/Linux
```

Per quanto concerne la versione di Python, a meno di casi particolari, su Raspbian OS 
dovrebbero essere installate due release di Python, la 2.x e la 3.x. La specifica 
minor version dipende dalla versione del sistema operativo. Nel caso di Raspbian OS Buster 
le versioni esatte sono:

1. Python 2.7.16 (attiva per default)
2. Python 3.7.3

Sul mio Raspberry Pi ho reso di default la versione 3.7.3 di Python, visto che questa 
è la versione richiesta per il corretto funzionamento del Bot che andremo a realizzare. 
Per rendere l’ultima versione di Python di default, è più che sufficiente aggiungere i 
seguenti alias su file ~/.bashrc

```bash
alias python='/usr/bin/python3'
alias pip=pip3
```

Una volta concluse le verifiche che riguardano Python, possiamo passare all'installazione
del resto dei componenti software.

```bash
$ sudo pip install pad4pi
$ sudo apt-get install pcscd
$ sudo apt-get install libccid
$ sudo apt-get install opensc
```

A questo punto, che i requisiti hardware e software di base sono soddisfatti, vediamo
com'è strutturato il progetto software.


# 3. Organizzazione del progetto
Il progetto è così organizzato.

1. **modules**: questa directory contiene i moduli Python per l'utilizzo del display LCD 16x2
        a. PCF8574.py: modulo per la gestione del bus i2c
        b. Adafruit_LCD1602.py: funzioni ad alto livello per le operazioni sul display LCD
2. **scripts**: questa directory contiene lo script Python **parse-gov-certs.py** il cui scopo 
è il download dei certificati Governativi Italiani, e lo script bash **auto-update-gov-certificates.sh**
il cui scopo è aggiungere sul sistema i certificati Governativi Italiani
3. **test_keypad_pin_lcd.py**: script Python per il test del funzionamento del Key Pad
4. **verify_ts_cns_pin.py**: script Python per la verifica del codice PIN sulla TS-CNS
5. **activate_relay_via_pin_code.py**: script Python che permette l'attiviazione dei relè inserendo
il codice PIN (1234), senza quindi interazione con la TS-CNS.
6. **activate_relay_via_ts_cns_pin.py**: script Python che permette l'attivazione dei relè inserendo
il codice PIN della TS-CNS.

Gli script **verify_ts_cns_pin.py** e **activate_relay_via_ts_cns_pin.py** sono quelli che
interagiscono con il lettore di Smart Card e la TS-CNS. Il resto degli script sono per fare il test sulla
corretta funzionalità del Key Pad e Relè, e accertarsi quindi che i collegamenti tra i vari
componenti stiano funzionando correttamente.
 
# 4. Quick start
Supponendo che abbiate montato tutto secondo lo schema elettrico indicato e che il vostro Raspberry Pi 
sia connesso alla rete, possiamo procedere con i seguenti step.

1. Accesso al Raspberry Pi via SSH o direttamente dal console. Consiglio di accedere con utenza 
diversa da root
2. Clonazione del repository amusarra/raspberry-pi-access-via-ts-cns
3. Aggiornamento dei certificati di sistema
4. Esecuzione del test



```bash
$ cd --
$ git clone https://github.com/amusarra/raspberry-pi-access-via-ts-cns.git
$ cd  raspberry-pi-access-via-ts-cns
$ cd scripts
$ sudo ./auto-update-gov-certificate.sh
```

La figura a seguire mostra l'output che dovreste ottenere eseguendo lo script che aggiunge i
certificati Governativi Italiani al sistema.

![Aggiunta dei Certificati Governativi al sistema](./docs/images/auto_update_gov_certificate.png)


L'aggiunta dei certificati Governativi Italiani al sistema è importante ai fini della validazione
del certificato digitale presente sulla TS-CNS. Nel caso questa operazione non venisse eseguita,
il processo di autenticazione non andrà mai a buon fine, anche nel caso in cui il PIN inserito
fosse corretto.

![Errore di validazione certificato digitale](./docs/images/errore_validazione_certificato_1.png)

A questo punto è tutto pronto per iniziare i test di funzionamento della soluzione. Consiglio di
procedere con l'esecuzione degli script Python, con lo stesso ordine mostrato nel capitolo
_3. Organizzazione del progetto_. Per eseguire gli script sarà sufficiente utilizzare la sintassi
`./nome_script_python.py`.
