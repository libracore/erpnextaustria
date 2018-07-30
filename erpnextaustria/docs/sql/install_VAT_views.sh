#!/bin/bash

# this script will load all VAT tables to the designated database

if [ "$1" != "" ]
  then
    mysql "$1" < viewATVAT_000.sql
    mysql "$1" < viewATVAT_022.sql
    mysql "$1" < viewATVAT_060.sql
    mysql "$1" < viewATVAT_065.sql
    mysql "$1" < viewATVAT_070.sql
    mysql "$1" < viewATVAT_072.sql
    
  else
    echo "Please provide the database schema name as first parameter"
fi
