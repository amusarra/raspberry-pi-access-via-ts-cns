#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script per comunicare con una Smart Card tramite comandi APDU usando pyscard.

Questo script invia comandi APDU specifici alla Smart Card per leggere dati personali.
È possibile utilizzare il parametro --debug per visualizzare informazioni dettagliate durante l'esecuzione.

Requisiti:
- Python 3.6 o superiore
- pyscard: libreria per la comunicazione con Smart Card
- colorama: per la colorazione del testo nel terminale

Installazione delle dipendenze:
    pip install pyscard colorama

Prerequisiti di sistema:
- macOS: librerie di sviluppo PCSC
- Linux: pacchetto pcscd e librerie di sviluppo
- Windows: driver per il lettore di Smart Card

Utilizzo:
    python read-ts-cns-data.py         # Esecuzione normale
    python read-ts-cns-data.py --debug # Modalità debug con informazioni dettagliate

Autore: Antonio Musarra <antonio.musarra[at]gmail.com>
"""

import argparse
import array
from smartcard.System import readers
from smartcard.util import toHexString
from colorama import Fore, Style, init

# Inizializza colorama per la colorazione del testo nel terminale
init(autoreset=True)

# Parsiamo gli argomenti
parser = argparse.ArgumentParser(description='Legge i dati personali da una TS-CNS.')
parser.add_argument('--debug', action='store_true', help='Abilita la modalità debug')
args = parser.parse_args()


# Definizione delle eccezioni personalizzate
class NoSmartCardReaderFound(Exception):
    pass


class NoSmartCardInserted(Exception):
    pass


# Funzione per stampare messaggi di debug
def debug_msg(message):
    global args
    if args.debug:
        print(f"{Fore.YELLOW}🐞🛠️ {message}")


# Funzione per stampare messaggi di successo
def success_msg(message):
    print(f"{Fore.GREEN}✅ {message}")

# Funzione per stampare errori
def warn_msg(message):
    print(f"{Fore.YELLOW}⚠️ {message}")


# Funzione per stampare errori
def error_msg(message):
    print(f"{Fore.RED}❌ {message}")


def send_apdu(connection, apdu):
    """Invia un comando APDU alla Smart Card e riceve la risposta."""
    debug_msg(f"Inviando APDU: {apdu}")

    try:
        response, sw1, sw2 = connection.transmit(apdu)
        status_str = f"SW1={sw1:02X}, SW2={sw2:02X}"
        debug_msg(f"Risposta: {toHexString(response)} {status_str}")
        return response, sw1, sw2
    except Exception as e:
        error_msg(f"Errore nell'invio dell'APDU: {e}")
        return [], 0, 0


def hex_to_string(hex_data):
    """Converte dati esadecimali in una stringa."""
    result = ""
    for i in range(0, len(hex_data), 2):
        if i + 1 < len(hex_data):
            # Prende due caratteri esadecimali e li converte in un carattere
            char_code = int(hex_data[i:i + 2], 16)
            # Verifica se il carattere è un ASCII stampabile
            if 32 <= char_code <= 126:
                result += chr(char_code)
            else:
                result += '.'
    return result


def get_ts_data(connection, debug=False):
    """Legge i dati personali dalla TS-CNS."""
    # Comandi APDU
    SELECT_MF = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00]
    SELECT_DF1 = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x11, 0x00]
    SELECT_EF_PERS = [0x00, 0xA4, 0x00, 0x00, 0x02, 0x11, 0x02]
    READ_BIN = [0x00, 0xB0, 0x00, 0x00, 0x00]

    # Seleziona il Master File (MF)
    response, sw1, sw2 = send_apdu(connection, SELECT_MF)
    if sw1 != 0x90 or sw2 != 0x00:
        error_msg(f"Errore durante la selezione del Master File: SW1={sw1:02X}, SW2={sw2:02X}")
        return None

    debug_msg("MF selezionato con successo")

    # Seleziona il Dedicated File (DF)
    response, sw1, sw2 = send_apdu(connection, SELECT_DF1)
    if sw1 != 0x90 or sw2 != 0x00:
        error_msg(f"Errore durante la selezione del DF: SW1={sw1:02X}, SW2={sw2:02X}")
        return None

    debug_msg("DF selezionato con successo")

    # Seleziona l'Elementary File (EF) contenente i dati personali
    response, sw1, sw2 = send_apdu(connection, SELECT_EF_PERS)
    if sw1 != 0x90 or sw2 != 0x00:
        error_msg(f"Errore durante la selezione dell'EF: SW1={sw1:02X}, SW2={sw2:02X}")
        return None

    debug_msg("EF selezionato con successo")

    # Leggi i dati binari dal file selezionato
    response, sw1, sw2 = send_apdu(connection, READ_BIN)

    if sw1 == 0x6C:  # Se la lunghezza è errata, riprova con la lunghezza corretta
        read_bin_with_length = [0x00, 0xB0, 0x00, 0x00, sw2]
        warn_msg(f"Riprovo con READ_BIN e lunghezza corretta: {read_bin_with_length}")
        response, sw1, sw2 = send_apdu(connection, read_bin_with_length)

    # Puoi anche aggiungere un controllo per il codice errore 67:00
    if sw1 == 0x67 and sw2 == 0x00:
        warn_msg("Errore 67:00 - Provo a leggere con lunghezza standard")
        # Prova con una lunghezza standard (ad esempio 0xFF o 0x80)
        read_bin_with_length = [0x00, 0xB0, 0x00, 0x00, 0xFF]
        response, sw1, sw2 = send_apdu(connection, read_bin_with_length)

    if sw1 != 0x90 or sw2 != 0x00:
        error_msg(f"Errore durante la lettura dei dati: SW1={sw1:02X}, SW2={sw2:02X}")
        return None

    debug_msg("Dati letti con successo")

    # Elabora e restituisci i dati letti
    hex_data = ''.join([f'{b:02X}' for b in response])

    # Aggiungi la decodifica
    decoded_data = decode_ts_data(response)

    return {
        'raw_data': response,
        'hex_data': hex_data,
        'string_data': hex_to_string(hex_data),
        'decoded_data': decoded_data
    }


def decode_ts_data(raw_data):
    """Decodifica i dati personali dalla TS-CNS interpretando i prefissi di lunghezza."""
    try:
        # Converti i dati raw in un array di byte
        dati_bytes = array.array('B', raw_data).tobytes()
        dati_ts = {}

        # Salta i primi 6 byte (dimensione)
        pos = 6

        # Leggi ogni campo con il suo prefisso di lunghezza
        # Emettitore
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['emettitore'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Data rilascio
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            data = dati_bytes[pos:pos + field_len].decode('ascii')
            dati_ts['data_emissione'] = f"{data[0:2]}/{data[2:4]}/{data[4:8]}"
        pos += field_len

        # Data scadenza
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            data = dati_bytes[pos:pos + field_len].decode('ascii')
            dati_ts['data_scadenza'] = f"{data[0:2]}/{data[2:4]}/{data[4:8]}"
        pos += field_len

        # Cognome
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['cognome'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Nome
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['nome'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Data nascita
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            data = dati_bytes[pos:pos + field_len].decode('ascii')
            dati_ts['data_nascita'] = f"{data[0:2]}/{data[2:4]}/{data[4:8]}"
        pos += field_len

        # Sesso
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['sesso'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Statura (potrebbe essere vuota)
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['statura'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Codice fiscale
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['codice_fiscale'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Cittadinanza
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['cittadinanza'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        # Comune nascita
        field_len = int(dati_bytes[pos:pos + 2], 16)
        pos += 2
        if field_len > 0:
            dati_ts['comune_nascita'] = dati_bytes[pos:pos + field_len].decode('ascii')
        pos += field_len

        return dati_ts

    except Exception as e:
        error_msg(f"Errore durante la decodifica: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return None


def dump_raw_data(raw_data):
    """Mostra una rappresentazione dettagliata dei dati grezzi per analisi."""
    ascii_dump = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in raw_data])

    debug_msg("Esadecimale:")
    # Mostra 16 byte per riga
    for i in range(0, len(raw_data), 16):
        hex_line = ' '.join([f'{raw_data[j]:02X}' for j in range(i, min(i + 16, len(raw_data)))])
        debug_msg(f"{i:04X}: {hex_line:48s}  {ascii_dump[i:i + 16]}")


def main():
    # Ottieni la lista dei lettori di smart card
    reader_list = readers()
    if args.debug:
        debug_msg(f"Lettori disponibili: {reader_list}")

    if len(reader_list) == 0:
        raise NoSmartCardReaderFound("Nessun lettore di smart card trovato")

    # Usa il primo lettore disponibile
    reader = reader_list[0]
    if args.debug:
        debug_msg(f"Usando il lettore: {reader}")

    # Crea una connessione con la smart card
    try:
        connection = reader.createConnection()
        connection.connect()
        if args.debug:
            debug_msg("Connessione alla smart card stabilita")

            # Mostra ATR (Answer To Reset)
            atr = connection.getATR()
            debug_msg(f"ATR: {toHexString(atr)}")
    except Exception as e:
        raise NoSmartCardInserted(f"Impossibile connettersi alla smart card: {e}")

    try:
        # Leggi i dati personali dalla TS-CNS
        ts_data = get_ts_data(connection, args.debug)

        if ts_data:
            debug_msg("Dati letti dalla Smart Card:")

            # Mostra dump completo in modalità debug
            if args.debug:
                dump_raw_data(ts_data['raw_data'])

            # Mostra dati decodificati
            if ts_data['decoded_data']:
                success_msg("Dati decodificati:")
                for field, value in ts_data['decoded_data'].items():
                    field_name = field.replace('_', ' ').capitalize()
                    print(f"  {field_name}: {value}")
            else:
                error_msg("Non è stato possibile decodificare i dati")
    finally:
        # Disconnetti dalla smart card
        try:
            connection.disconnect()
            if args.debug:
                success_msg("Disconnessione dalla smart card completata")
        except Exception as e:
            if args.debug:
                error_msg(f"Errore durante la disconnessione: {e}")


if __name__ == "__main__":
    main()
