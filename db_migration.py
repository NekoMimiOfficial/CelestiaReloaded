import Tools.DBCables as cables
from NekoMimi import utils as nm
import os

def main():
    sqcbl= cables.Cables("celestia_datastore.db")
    sqcbl.connect()
    db_dir= nm.get_conf_dir_unix()+ "/NekoPyReg"
    contents= os.listdir(db_dir)
    i= 0
    while i < len(contents):
        for item in contents:
            if not item.startswith("Celestia-Guilds"):
                contents.pop(i)
                break
            i += 1

    print("processing guilds:")
    print("~~~~~~~~~~~~~~~~~~")
    print(contents)
    print()

    idb= []
    print("constructing guild tables:")
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    for item in contents:
        data_dir= db_dir+ "/"+ item
        if not os.path.exists(data_dir+ "/lb"):
            continue
        guild_id= item.split("-", 2)[2].strip()
        lb= []
        get_lb= nm.read(data_dir+ "/lb")
        for line in get_lb.split("\n"):
            try:
                score, suid, name = line.strip().split(',')
                lb.append({'user_id': suid, 'score': int(score), 'name': name})
            except ValueError:
                continue

        print(f"ID:       {guild_id}")

        for usr in lb:
            idb.append({'uid': int(usr['user_id']),'gid': int(guild_id), 'pts': int(usr['score']),'dname': usr['name']})
    print()

    print("saving userdata into db:")
    print("~~~~~~~~~~~~~~~~~~~~~~~~")

    bank= {}
    for sv in idb:
        bank[sv['uid']]= 0

    i= 0
    while i < len(idb):
        bank[idb[i]["uid"]] = bank[idb[i]["uid"]]+ idb[i]['pts']
        i += 1

    for sv in idb:
        print(f"USER:     {sv['dname']} @ {sv['uid']} > {sv['pts']} (bank: {bank[sv['uid']]})")
        sqcbl.update_user(sv['uid'], sv['gid'], sv['dname'], sv['pts'], bank[sv['uid']], 50, bank[sv['uid']], 0)

    print()


if __name__ == "__main__":
    main()
