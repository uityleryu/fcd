#!/bin/sh

EEPROM_BIN=e.b
EEPROM_TXT=e.t
EEPROM_SIGNED=e.b
EEPROM_CHECK=e.c

if [ -f /tmp/${EEPROM_BIN}.$1 ]; then
    rm /tmp/${EEPROM_BIN}.$1
    echo "Delete /tmp/${EEPROM_BIN}.$1"
else
    echo "No /tmp/${EEPROM_BIN}.$1"
fi

if [ -f /tmp/${EEPROM_TXT}.$1 ]; then
    rm /tmp/${EEPROM_TXT}.$1
    echo "Delete /tmp/${EEPROM_TXT}.$1"
else
    echo "No /tmp/${EEPROM_TXT}.$1"
fi

if [ -f /tmp/${EEPROM_SIGNED}.$1 ]; then
    rm /tmp/${EEPROM_SIGNED}.$1
    echo "Delete /tmp/${EEPROM_SIGNED}.$1"
else
    echo "No /tmp/${EEPROM_SIGNED}.$1"
fi

if [ -f /tmp/${EEPROM_CHECK}.$1 ]; then
    rm /tmp/${EEPROM_CHECK}.$1
    echo "Delete /tmp/${EEPROM_CHECK}.$1"
else
    echo "No /tmp/${EEPROM_CHECK}.$1"
fi
