#export PATH=/home/queunet/OTB-8.0.0-Linux64/bin:$PATH
export PATH=$PATH:/home/queunet/OTB-8.0.0-Linux64/bin
Path2tiles="/media/queunet/WD/dir_3_S2_r_2019_44QKE"

listimagesZIP=$(echo `ls $Path2tiles/SENT*.zip`)
datemoins1=""
NDVImoin1=""
namelistdate="/media/queunet/WD/list_date/ListDate_S2_QKE_from_october_to_july.csv"
echo "dates" >> $namelistdate

for namezip in $listimagesZIP
do
pathJPG=`unzip -l $namezip | grep ALL.jpg`
pathJPG=`echo $pathJPG | rev | cut -d" " -f1 | rev`;
nameJPG=`echo $pathJPG | rev | cut -d"/" -f1 | rev`;
nameProduct=`echo $pathJPG | cut -d"/" -f1`;
date=`echo $nameJPG|cut -d"_" -f2`;
date=`echo $date|cut -d"-" -f1`;
tuile=`echo $nameJPG|cut -d"_" -f4`;

nameB4=${pathJPG//QKL_ALL.jpg/FRE_B4.tif}
nameB8=${pathJPG//QKL_ALL.jpg/FRE_B8.tif}
nameCloudMask=${nameJPG//QKL_ALL.jpg/CLM_R1.tif}
PathCloudMask=$nameProduct/MASKS/$nameCloudMask

mkdir $Path2tiles/$tuile
unzip -n -j $namezip $nameB4 -d $Path2tiles/$tuile
unzip -n -j $namezip $nameB8 -d $Path2tiles/$tuile
unzip -n -j $namezip $PathCloudMask -d $Path2tiles/$tuile

nameB8=`echo $nameB8|cut -d"/" -f2`;
nameB4=`echo $nameB4|cut -d"/" -f2`;
NDVI=$Path2tiles/$tuile/${nameB4//FRE_B4.tif/NDVI.tif}

otbcli_BandMath -il $Path2tiles/$tuile/$nameB8 $Path2tiles/$tuile/$nameB4 $Path2tiles/$tuile/$nameCloudMask -out $NDVI -exp " ( im1b1 - im2b1 ) / (im1b1 + im2b1 ) * 100 * ( im3b1 == 0 )"
gdal_edit.py -a_nodata 0 $NDVI

if [ "$date" -eq "$datemoins1" ];
then
gdal_merge.py -a_nodata 0 -o ${NDVI//.tif/temp.tif} $NDVI $NDVImoin1
rm $NDVImoin1
rm ${NDVImoin1//.tif/nodat255.tif}
mv ${NDVI//.tif/temp.tif} $NDVI
else
echo $date >> $namelistdate
fi

otbcli_ManageNoData -in $NDVI -out ${NDVI//.tif/nodat255.tif} -mode changevalue -mode.changevalue.newv 255

rm $Path2tiles/$tuile/$nameB4
rm $Path2tiles/$tuile/$nameB8
rm $Path2tiles/$tuile/$nameCloudMask
datemoins1=$date
NDVImoin1=$NDVI
done

listimagesNDVInodata0=$(echo `ls $Path2tiles/$tuile/*NDVI.tif`)
Nb=$(echo $listimagesNDVI| grep -o " "| wc -l)
listimagesNDVInodata255=$(echo `ls $Path2tiles/$tuile/*NDVInodat255.tif`)

gdalbuildvrt -separate $Path2tiles/$tuile/NDVI.vrt $listimagesNDVInodata0
gdal_edit.py -a_nodata 0 $Path2tiles/$tuile/NDVI.vrt
gdalbuildvrt -separate $Path2tiles/$tuile/NDVInodata255.vrt $listimagesNDVInodata255


otbcli_BandMathX -il $Path2tiles/$tuile/NDVI.vrt -out $Path2tiles/$tuile/MaxNDVI.tif -exp "vmax(im1)"

otbcli_BandMathX -il $Path2tiles/$tuile/NDVInodata255.vrt -out $Path2tiles/$tuile/MinNDVI.tif -exp "vmin(im1)"

otbcli_BandMath -il $Path2tiles/$tuile/MinNDVI.tif $Path2tiles/$tuile/MaxNDVI.tif -out $Path2tiles/$tuile/MaxMinusMinNDVI.tif -exp "im2b1 - im1b1"
