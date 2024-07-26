<div align="center">

<h1>우리 어디서 만나🌟</h1>

<br />

친구들과 어렵게 만남 약속을 잡았는데

각자 사는 곳이 달라 **만남 장소를 정하기 어려웠던 경험**,

경기도민을 고려하지 않은 약속 장소에 가기 위해

**대중교통을 타고 긴 시간 이동했던 경험**이 있으신가요?

그래서 만들었습니다.



![logo2](https://github.com/user-attachments/assets/cf43b85b-3525-41fc-9ded-d9ee382bb22a)

<h3> 알아서 잘 딱 깔끔하고 센스있게 만남 장소를 정해주는 웹서비스,</h3>
<h2> 우리 어디서 만나 </h2>

<br />

✔️ **단순히 사용자들의 중간 지점을 찾아주는 것이 아니라, 핫플과 맛집의 빈도까지 종합적으로 고려하여 추천해줘요!**
<br />
✔️ **약속 장소는 아직은 서울 지하철역으로 한정되어 있어요🥺**

</br>

[✨ <우리 어디서 만나> 사용해보기](https://www.where2meet.site/)

</div>

<br />

# 목차

### [1. 주요 기능 설명]

### [2. 기술 스택]

### [3. 팀원 소개]

<br />

# 주요 기능 설명
## [MainPage]
### [ 검색 기능 ] 
![Untitled (1)](https://github.com/user-attachments/assets/c29a4ae3-f6ab-4225-813c-dcceaf08b687)
![Untitled](https://github.com/user-attachments/assets/568b0853-ef88-4a2d-835c-6e08da8a1086)

- 출발지 주소를 최대 5개까지 입력할 수 있어요.
- 최적의 약속 장소를 찾기 위해, 만남과 관련된 키워드를 선택할 수 있어요.

## [ ResultPage]
<img width="1710" alt="Untitled (2)" src="https://github.com/user-attachments/assets/0f1a78c7-c607-4eb5-bff1-f0a9367e5952">

### [ 약속 장소 추천 기능 ]

- 사용자가 입력한 주소들의 중간 지점을 계산하고 그 주위의 지하철 역 중 사용자가 고른 factor와 가장 적합한 장소를 추천해줘요.

### [ chatgpt 한줄 요약 기능 ]

- 선정된 약속 장소가 만남에 적합한 이유를 gpt가 설명해줘요. 

### [ 관련 장소 추천 및 길찾기 ]

- 약속 장소 근처에서 갈 만한 곳을 캐치테이블, 네이버맵, 카카오맵 검색으로 바로 확인할 수 있어요.  
- 카카오맵 길찾기로 바로 이동할 수 있어요. 

### [ 공유하기 ]
<img width="1706" alt="Untitled (3)" src="https://github.com/user-attachments/assets/74b9d0ee-9c68-4605-b0e3-003426882459">

- 결과를 클립보드에 복사하거나 카카오톡으로 공유할 수 있어요.

<br />

# ⚒️ 기술 스택

## API Integration

### ODSay API

![image](https://github.com/user-attachments/assets/12e7e74f-932c-4c77-817a-76667d6640f5)


- 대중교통 길찾기 API를 통해 소요 시간을 받음
- 지도 위 대중교통 경로를 그림

### Kakao API

![image](https://github.com/user-attachments/assets/c2d9e7cc-b688-49c3-8311-071fd95f8904)

- 사용자들의 출발 위치들로부터 가장 가까운 역을 계산함
- 지하철역 주변의 음식점 등의 개수를 조사함
- 지도를 띄움

### OPENAI API

![image](https://github.com/user-attachments/assets/f1b1daae-1fe5-44a5-bca6-4c07cc026f19)

- 만나는 장소가 적합한 이유를 알려줌.

## Deployment and Operations

### Vercel

![image](https://github.com/user-attachments/assets/6cbff580-7aec-4b95-b57c-9dee240fc560)


- 프론트 배포

### AWS

![image](https://github.com/user-attachments/assets/47f3198d-cabb-401d-a7b5-2a8493ee061e)

- 백 배포, EC2 고정 IP
- 도메인 구입하여 HTTPS 적용


<br />

# 🏃‍♂️ 팀원 소개

<table >
  <tr height="130px">
    <td align="center" width="130px">
      <a href="https://github.com/minseo25"><img src="src/assets/images/고양1.jpg" style="border-radius:50%"/></a>
    </td>
    <td align="center" width="130px">
      <a href="https://github.com/Yeeunleel"><img src="src/assets/images/고양2.jpeg"  style="border-radius:50%" /></a>
    </td>
    <td align="center" width="130px">
      <a href="https://github.com/jihochang03"><img src="src/assets/images/고양3.jpg"  style="border-radius:50%"/></a>
    </td>
    <td align="center" width="130px">
      <a href="https://github.com/rokiki2"><img src="src/assets/images/고양4.jpg"  style="border-radius:50%"/></a>
    </td>
  </tr>
  
  <tr height="50px">
    <td align="center" width="130px">
      <a href="https://github.com/minseo25">김민서</a>
    </td>
    <td align="center" width="130px">
      <a href="https://github.com/Yeeunleel">이예은</a>
    </td>
    <td align="center" width="130px">
      <a href="https://github.com/jihochang03">장지호</a>
    </td>
    <td align="center" width="130px">
      <a href="https://github.com/rokiki2">이록희</a>
    </td>
  </tr>
</table>

<br />

## 😺 김민서 (FE)

- 응원단장(with 구름이)
- 깃허브: https://github.com/minseo25

## 😸 이예은 (FE)

- 디자이너
- 깃허브: https://github.com/Yeeunleel

## 😻 장지호 (BE)

- 막내온탑
- 깃허브: https://github.com/jihochang03

## 😽 이록희 (BE)

- 일꾼1
- 깃허브: https://github.com/rokiki2


<br />
