from wcferry import Wcf
print("Creating WCF client...")
wcf = Wcf()
print("INIT OK!")
print("Msg types:", wcf.get_msg_types())
