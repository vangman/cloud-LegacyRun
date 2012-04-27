#!/bin/sh

if [ -z "$STRATUSLAB_NC" ]; then
	echo "Not running inside a StratusLab cluster. Exiting..."
	exit 127
fi

if [ $STRATUSLAB_NC = "0" ]; then 

export BIN_EXEC=`which mm5`

datetod=`date +%Y%m%d`00

listhours=`seq -w 00 06 72`

### Get data from NOMADS server
for hour in $listhours;
do
	wget -O GRIB$hour "http://$NOMADSERVER/cgi-bin/filter_gfs.pl?file=gfs.t00z.pgrbf$hour.grib2&var_HGT=on&var_UGRD=on&var_VGRD=on&var_TMP=on&var_RH=on&var_PRMSL=on&var_PRES=on&subregion=&leftlon=-30&rightlon=60&toplat=70&bottomlat=20&dir=%2Fgfs.$datetod"
	sleep 15
done

### Decode GRIB files 
for hour in $listhours;
	do
		if [ ! -f GRIB$hour ]; then
			echo "ERROR: GRIB$hour not available or zero length."
			exit -1
		fi
	done
	
for hour in $listhours;
	do
		wgrib2  -vt GRIB$hour  >validtime_$hour
		wgrib2 GRIB$hour |egrep '$TMPLEVELS'| wgrib2 -i GRIB$hour  -text tmp_$hour
		wgrib2 GRIB$hour |egrep '$HGTLEVELS'| wgrib2 -i GRIB$hour  -text hgt_$hour
		wgrib2 GRIB$hour |egrep '$UGRDLEVELS'| wgrib2 -i GRIB$hour  -text ugrd_$hour
		wgrib2 GRIB$hour |egrep '$VGRDLEVELS'| wgrib2 -i GRIB$hour  -text vgrd_$hour
		wgrib2 GRIB$hour |egrep '$RHLEVELS'| wgrib2 -i GRIB$hour  -text rh_$hour
		wgrib2 GRIB$hour |egrep '$PRMSL'| wgrib2 -i GRIB$hour  -text msl_$hour
		wgrib2 GRIB$hour |egrep '$TMP'| wgrib2 -i GRIB$hour  -text sst_$hour

		ln -fs  tmp_$hour fort.10
		ln -fs  hgt_$hour fort.11
		ln -fs  ugrd_$hour fort.12
		ln -fs  vgrd_$hour fort.13
		ln -fs  rh_$hour fort.14
		ln -fs  msl_$hour fort.15
		ln -fs  sst_$hour fort.16
		ln -fs OUTPUT$hour fort.24
		ln -fs validtime_$hour fort.55

		grib2mm5.e
    done

for hour in $listhours;
	do
readoutput_nomad19.e <<EOF
OUTPUT$hour
EOF
	done


    ### Prepare environment
	today=`date +%F`
	
	# Start day
	m1=`date +%m`
	d1=`date +%d`
	y1=`date +%Y`
	
	# End forecast day (3 days ahead in the future)
	ey=$(date --date "$today + $FORECASTDAYS days" +%Y)
	em=$(date --date "$today + $FORECASTDAYS days" +%m)
	ed=$(date --date "$today + $FORECASTDAYS days" +%d)

	# Generate namelist input 
	sed -e "s/SYEAR/$y1/" namelist_regrid.input | \
	sed -e "s/SMONTH/$m1/" | \
	sed -e "s/SDAY/$d1/" | \
	sed -e "s/EYEAR/$ey/" | \
	sed -e "s/EMONTH/$em/" | \
	sed -e "s/EDAY/$ed/"> namelist.input

    ### Run binary
	regridder

   	# Prepare namelist input
	sed -e "s/SYEAR/$y1/" namelist_interpf.input | \
	sed -e "s/SMONTH/$m1/" | \
	sed -e "s/SDAY/$d1/" | \
	sed -e "s/EYEAR/$ey/" | \
	sed -e "s/EMONTH/$em/" | \
	sed -e "s/EDAY/$ed/" > namelist.input

    ### Run binary
	interpf

	sed -e "s/LIFY/$y1/" mmlif.input | \
	sed -e "s/LIFM/$m1/" | \
	sed -e "s/LIFD/$d1/" > mmlif

	ln -s $BIN_EXEC mm5

    ### Run the binary
	mpirun -machinefile /tmp/machinefile  -np $STRATUSLAB_CMAX_CORES ./mm5

    ### Post-process 

    ### Store in data repository

fi

