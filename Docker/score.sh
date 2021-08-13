#!/bin/sh

TMP="tmpdir"

# Get list of prediction files and save into CSV.
find ${TMP}/* -type f > inFileList.csv
while read i
do
    bn=$( basename ${i} );
    sub=${bn%.nii.gz};
    id=$( basename $sub | tail -c 6 );
    gt="RSNA_ASNR_MICCAI_BraTS2021_ValidationGT/BraTS2021_${id}_seg.nii.gz";
    echo "${id},${i},${gt}" >> ${TMP}/inputData.csv
done < inFileList.csv


# Compute metrics for each case.
while read i
do
    fields=(${i//,/ })
    id=${fields[0]}
    pred=${fields[1]}
    gold=${fields[2]}

    /work/CaPTk/bin/Utilities \
        -i ${gold} \
        -lsb ${pred} \
        -o scores/${id}_stats.csv;

    if [ ! -f scores/${id}_stats.csv ];
	then
        # file does not exist
        echo $i >> invalid_input_data.csv;
    else
        # the file exists
        if [ ! -s scores/${id}_stats.csv ];   
        then
            echo $i >> invalid_input_data.csv;
        fi
    fi
done < ${TMP}/inputData.csv
