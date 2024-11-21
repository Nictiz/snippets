# function could be added into ~/.bash_profile if you source that into the macOS default shell zsh using ~/.zshrc
# uses awk to help markup a list of git repositories and the branches they are in. Example output:
#% git-branches        
#Repository                               Branch
#---------------------------------------- ------------------------------
#Geboortezorg                             master
#HL7-mappings                             master
#Medicatieproces                          master
#Nictiz-DSTU2                             master
#Nictiz-FHIR-IG                           master
#Nictiz-FHIR-IG-R4                        main
#Nictiz-R4-LabExchange                    main
#Nictiz-R4-Vaccination-Immunization       main
#Nictiz-R4-zib2020                        main
function git-branches {
  nictizgits=~/Development/GitHub/Nictiz
  echo Repository,Branch>~/gb.txt
  echo ----------------------------------------,------------------------------>>~/gb.txt
  for d in `ls $nictizgits`; do
    #  echo ::: $d
    if [ -d $nictizgits/$d/.git ]; then
      b=`git -C $nictizgits/$d branch --show-current`
      echo "$d,$b" >>~/gb.txt
    fi
  done
  awk -F , '{$1 = sprintf("%-40s", $1)} 1' ~/gb.txt
  rm ~/gb.txt
};
