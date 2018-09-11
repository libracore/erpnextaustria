#!/bin/bash

# this script will load all VAT tables to the designated database

if [ "$1" != "" ]
  then
    mysql "$1" < viewATVAT_000.sql
    mysql "$1" < viewATVAT_011.sql
    mysql "$1" < viewATVAT_017.sql
    mysql "$1" < viewATVAT_021.sql
    mysql "$1" < viewATVAT_022.sql
    mysql "$1" < viewATVAT_029.sql
    mysql "$1" < viewATVAT_057.sql
    mysql "$1" < viewATVAT_060.sql
    mysql "$1" < viewATVAT_061.sql
    mysql "$1" < viewATVAT_065.sql
    mysql "$1" < viewATVAT_066.sql
    mysql "$1" < viewATVAT_070.sql
    mysql "$1" < viewATVAT_072.sql
    mysql "$1" < viewATVAT_083.sql
    
  else
    echo "Please provide the database schema name as first parameter"
fi
