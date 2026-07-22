Bloxorz Project - Ursina Engine (Python)

CAU TRUC THU MUC
  core/
    state.py          Board, Switch, SplitSwitchDecl, State (immutable) dung cho solver
    board.py          Doc file stage (.txt) -> Board
    bloxorz_core.py    BloxorzCore (mutable) dung cho GUI/choi tay
  solvers/
    bfs_solver.py, dfs_solver.py, ucs_solver.py, astar_solver.py
  stages/
    stage1.txt ... stage10.txt   10 man choi do kho tang dan
  main.py              Chay game (Ursina)

DIEU KHIEN TRONG GAME
  W A S D            di chuyen khoi (hoac cube dang active khi da split)
  Space              doi cube dang dieu khien (chi khi da tach khoi)
  R                  choi lai man hien tai
  Nut Solve BFS/DFS/UCS/A*   tu dong giai va phat animation
  Nut Load Stage     mo hop thoai chon file stage khac trong thu muc stages/
  Nut Reset          choi lai man hien tai

DINH DANG FILE STAGE (.txt)

Phan 1 - luoi (bat buoc), moi o cach nhau boi khoang trang:
  0 = void         khong co gach
  1 = floor        san thuong
  2 = goal         dich (thang khi dung DUNG len day)
  S = start        vi tri xuat phat (tinh la floor)
  3 = fragile      gach de vo (dung len la vo, nam qua thi an toan)
  4 = bridge       cau (dong = nhu void, mo = nhu floor)
  5 = soft switch  kich hoat du dung hay nam de len
  6 = heavy switch chi kich hoat khi DUNG dung len
  7 = split switch chi kich hoat khi DUNG dung len -> tach thanh 2 cube 1x1x1

Phan 2 - khai bao switch/bridge/split (tuy chon), sau 1 dong trong hoac ngay
sau dong luoi cuoi cung:

  BRIDGE <group> <r1> <c1> <r2> <c2> ...
      Khai bao cac o thuoc nhom cau <group>. Co the khai nhieu dong BRIDGE
      cung group de gop lai thanh 1 nhom lon hon.

  SWITCH <r> <c> <SOFT|HEAVY> <TOGGLE|PERMANENT> <group> [OPEN|CLOSED]
      Khai bao switch tai (r, c). [OPEN|CLOSED] chi bat buoc khi mode la
      PERMANENT (trang thai cau SAU KHI switch duoc kich hoat).

  INIT <group> <OPEN|CLOSED>
      (Tuy chon) trang thai ban dau cua nhom cau, mac dinh la CLOSED.

  SPLIT <r> <c> <target_a_r> <target_a_c> <target_b_r> <target_b_c>
      Khai bao split switch tai (r, c) - phai KHOP voi vi tri o token 7 tren
      luoi. Khi khoi DUNG len dung o nay, no tach thanh 2 cube 1x1x1, dich
      chuyen toi target_a / target_b.

LUU Y QUAN TRONG KHI TU THIET KE MAN CHOI:
  - Toa do (r, c) trong SWITCH/SPLIT PHAI khop chinh xac voi vi tri ky tu
    5/6/7 tren luoi. Neu lech, o van hien mau nhung se khong kich hoat dung
    cho, hoac nguoc lai o khong to mau nhung lai kich hoat duoc.
  - Tranh thiet ke hanh lang qua hep (1-2 hang/cot) - khoi Bloxorz lan theo
    kieu dung/nam xen ke nen co quy luat "chan le" ve vi tri co the dung
    len duoc; hanh lang hep de khien mot so o KHONG BAO GIO dung len duoc
    du ban tuong la co duong di. Nen danh gia man choi bang cach chay thu
    BFS/UCS truoc khi coi la hoan chinh.

GIOI HAN DA BIET:
  Split switch (token 7) hien chi hoat dong khi choi tay (BloxorzCore).
  Cac solver (BFS/DFS/UCS/A*, xem core/state.py + solvers/) coi o split
  switch nhu san thuong, khong mo phong duoc trang thai "da tach khoi".
  Vi vay khi thiet ke man choi co dung split switch, nen dat no o mot
  nhanh phu KHONG nam tren duong di ngan nhat toi dich - de nut Solve
  van hoat dong dung, con split switch la tinh nang choi tay/mo rong.
