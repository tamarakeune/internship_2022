#export PATH=/home/queunet/OTB-8.0.0-Linux64/bin:$PATH
export PATH=$PATH:/home/queunet/OTB-8.0.0-Linux64/bin

#NDWI=VENUS-XS_20200106-051835-000_L2A_KUDALIAR_C_V2-2_NDWI.tif
#nameVENUSBCKGRD=20200106_VENUS-XS.vrt

PathNDWI="/media/queunet/WD/dir_3_venus_r_2020/KUDALIAR"

for nameVENUSBCKGRD in *.vrt;
do
date=`echo "$nameVENUSBCKGRD"|cut -d"_" -f1`;

### fabrique tes NDWI
otbcli_BandMath -il $PathNDWI/VENUS-XS_${date}*NDWI.tif -out ${date}_maskEau.tif -exp "im1b1 > 20" # ... dont tu fais varier le $threshold pour essayer de voir à vu de nez la meilleure valeur.
#ajoute cette ligne qui va creer des polygones pour les zones eau (=1), mais pas de polygone pour les zones pas eau (=0) grâce à l'option -nomask -mask
gdal_polygonize.py -nomask -mask ${date}_maskEau.tif ${maskEau//.tif/.geojson} -b 1 -f "GeoJSON" ${date}_maskEau.tif ${date}_DN


### fait tes backgrounds IR/R/V en png comme tu sais faire
gdal_translate -of  PNG -ot Byte -b 4 -scale 0 250 -outsize 100% 100% $nameVENUSBCKGRD  B4.png #ici, scale c'est pour la couleur: comme dans qgis 0 à 2500 pour avoir de belles couleures, pas trop sombres ou claires... faut que la b 4 soit la bande 4, donc rouge

gdal_translate -of  PNG -ot Byte -b 3 -scale 0 250 -outsize 100% 100% $nameVENUSBCKGRD B3.png #idem
gdal_translate -of  PNG -ot Byte -b 2 -scale 0 250 -outsize 100% 100% $nameVENUSBCKGRD B2.png #idem

# create a VRT image from the chosen 3 bands
gdalbuildvrt -separate ${nameVENUSBCKGRD//.vrt/png.vrt} B4.png  B3.png B2.png 


resize="1000%"
#### extraire l'endroit: faut encore récuperer les coordonnées qui entourent tes shp

Yminlocal=1996318.9
Xminlocal=252976.6
Ymaxlocal=1996781.5
Xmaxlocal=253997.2


gdalbuildvrt ${nameVENUSBCKGRD//.vrt/zoom.vrt} ${nameVENUSBCKGRD//.vrt/png.vrt} -te $Xminlocal $Yminlocal $Xmaxlocal $Ymaxlocal
gdal_translate -of PNG -outsize 1000% 1000%   ${nameVENUSBCKGRD//.vrt/zoom.vrt} ${nameVENUSBCKGRD//.vrt/zoom.png}



gdalwarp -te $Xminlocal $Yminlocal $Xmaxlocal $Ymaxlocal ${date}_maskEau.tif ${date//.tif/zoom.tif}_maskEauzoom.tif
gdal_translate -of PNG -outsize 1000% 1000%  -ot Byte -b 1 -scale 0 1 -a_nodata 0 ${date//.tif/zoom.tif}_maskEauzoom.tif ${date//.tif/.png}_maskEauzoompng.png
convert ${date//.tif/.png}_maskEauzoompng.png -fill blue -opaque white -resize $resize ${date//.tif/.png}_maskEauzoompng_blue.png


composite ${date//.tif/.png}_maskEauzoompng_blue.png ${nameVENUSBCKGRD//.vrt/zoom.png}  ${date//.tif/.png}_maskEauzoompng_blue.png

width=`identify -format %w ${nameVENUSBCKGRD//.vrt/zoom.png}`
sizetext=`perl -E "say (int($width / 15))"`
sizetext=`echo $sizetext|cut -d"." -f1`

convert  ${date//.tif/.png}_maskEauzoompng_blue.png -transparent black -fill white -pointsize $sizetext -font Bookman-DemiItalic -draw "text 250,100 'Venus $date ' " ${date//.tif/.png}_maskEauzoompng_blue_date.png

done
#convert -delay 80 -loop 0 *_maskEauzoompng_blue_date.png animation.gif
