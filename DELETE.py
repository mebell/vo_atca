flare_stars =     ['Wolf424',
                   'YZ_CMi',
                   'YZCMi',
                   'YZ CMi',
                   'CN_Leo',
                   'CNLeo',
                   'CN Leo',
                   'V1054Oph',
                   'V645Cen',
                   'ROSS1280',
                   'DM-216267',
                   'V1216Sgr',
                   'HR_1099',
                   'HR 1099',
                   'HR1099',
                   'CF_Tuc',
                   'CFTuc',
                   'CF Tuc',
                   'AT_Mic',
                   'AT Mic',
                   'ATMic',
                   'AU_Mic',
                   'AUMic',
                   'AU Mic',
                   'UV_Cet',
                   'UV Cet',
                   'Flare from UV Cet',
                   'UVCet',
                   'HD 8357',
                   'HD_8357',
                   'HD8357',
                   'CC Eri',
                   'CC_Eri',
                   'CCEri',
                   'GT Mus',
                   'GT_Mus',
                   'GTMus']



name = "flare from HR1099" 
if name is not None:
   for star in flare_stars:
      print star, name
      if star in name:
	 print "Yes"
	 

