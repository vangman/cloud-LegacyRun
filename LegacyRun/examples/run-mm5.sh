#!/bin/sh

export BIN_EXEC=/opt/MM5-3.7.4-x86_64-INTEL/bin/mm5

datetod=`date +%Y%m%d`00

listhours=`seq -w 00 06 72`

### Get data from NOMADS server
for hour in $listhours;
do
	wget -O GRIB$hour   "http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs.pl?file=gfs.t00z.pgrbf$hour.grib2&var_HGT=on&var_UGRD=on&var_VGRD=on&var_TMP=on&var_RH=on
&var_PRMSL=on&var_PRES=on&subregion=&leftlon=-30&rightlon=60&toplat=70&bottomlat=20&dir=%2Fgfs.$datetod"
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


		wgrib2 GRIB$hour |egrep '(:TMP:1000|:TMP:950|:TMP:950|:TMP:900|:TMP:850|:TMP:800|:TMP:750|:TMP:700|:TMP:650|:TMP:600|:TMP:550|:TMP:500|:TMP:450|:TMP:400|:TMP:350|:TMP:300|:TMP:250|:TMP:200|:TMP:150|:TMP:100 )'| wgrib2 -i GRIB$hour  -text tmp_$hour

		wgrib2 GRIB$hour |egrep '(:HGT:1000|:HGT:950|:HGT:950|:HGT:900|:HGT:850|:HGT:800|:HGT:750|:HGT:700|:HGT:650|:HGT:600|:HGT:550|:HGT:500|:HGT:450|:HGT:400|:HGT:350|:HGT:300|:HGT:250|:HGT:200|:HGT:150|:HGT:100 )'| wgrib2 -i GRIB$hour  -text hgt_$hour

		wgrib2 GRIB$hour |egrep '(:UGRD:1000|:UGRD:950|:UGRD:950|:UGRD:900|:UGRD:850|:UGRD:800|:UGRD:750|:UGRD:700|:UGRD:650|:UGRD:600|:UGRD:550|:UGRD:500|:UGRD:450|:UGRD:400|:UGRD:350|:UGRD:300|:UGRD:250|:UGRD:200|:UGRD:150|:UGRD:100 )'| wgrib2 -i GRIB$hour  -text ugrd_$hour

		wgrib2 GRIB$hour  |egrep '(:VGRD:1000|:VGRD:950|:VGRD:950|:VGRD:900|:VGRD:850|:VGRD:800|:VGRD:750|:VGRD:700|:VGRD:650|:VGRD:600|:VGRD:550|:VGRD:500|:VGRD:450|:VGRD:400|:VGRD:350|:VGRD:300|:VGRD:250|:VGRD:200|:VGRD:150|:VGRD:100 )'| wgrib2 -i GRIB$hour  -text vgrd_$hour

		wgrib2 GRIB$hour |egrep '(:RH:1000|:RH:950|:RH:950|:RH:900|:RH:850|:RH:800|:RH:750|:RH:700|:RH:650|:RH:600|:RH:550|:RH:500|:RH:450|:RH:400|:RH:350|:RH:300|:RH:250|:RH:200|:RH:150|:RH:100 )'| wgrib2 -i GRIB$hour  -text rh_$hour

		wgrib2 GRIB$hour |egrep '(:PRMSL:mean )'| wgrib2 -i GRIB$hour  -text msl_$hour
		wgrib2 GRIB$hour |egrep '(:TMP:surface)'| wgrib2 -i GRIB$hour  -text sst_$hour

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

if [ $STRATUSLAB_NC = "0" ]; then 

    ### Prepare environment
	today=`date +%F`
	
	# Start day
	m1=`date +%m`
	d1=`date +%d`
	y1=`date +%Y`
	
	# End forecast day (3 days ahead in the future)
	ey=$(date --date "$today + 3 days" +%Y)
	em=$(date --date "$today + 3 days" +%m)
	ed=$(date --date "$today + 3 days" +%d)

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

