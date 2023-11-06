export LC_ALL=C.UTF-8
export LANG=C.UTF-8

common_dict_info="$COMMON_DICT"
IFS=':' read -r -a common_dict <<< "$common_dict_info"

addr=$(python3 -c "import json; data = $common_dict_info; print(data['addr'])")
dnn=$(python3 -c "import json; data = $common_dict_info; print(data['dnn'])")
dev=$(python3 -c "import json; data = $common_dict_info; print(data['dev'])")
addr2=$(python3 -c "import json; data = $common_dict_info; print(data['addr2'])")

echo "addr: $addr"
echo "dnn: $dnn"
echo "dev: $dev"
echo "addr: $addr2"

python3 /mnt/upf/tun_if.py --tun_ifname "$dev" --ipv4_range "$addr" --ipv6_range "$addr2"
# python3 /mnt/upf/tun_if.py --tun_ifname ogstun2 --ipv4_range $UE_IPV4_IMS --ipv6_range 2001:230:babe::/48 --nat_rule 'no'
