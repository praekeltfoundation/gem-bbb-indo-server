cd "${INSTALLDIR}/${NAME}/bimbingbung/"
manage="${VENV}/bin/python ${INSTALLDIR}/${NAME}/bimbingbung/manage.py"

$manage migrate --settings=bimbingbung.settings.production

# process static files
$manage compress --settings=bimbingbung.settings.production
$manage collectstatic --noinput --settings=bimbingbung.settings.production
