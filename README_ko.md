# Claude Code Changelog Dashboard

[![Auto Sync](https://img.shields.io/badge/sync-매시간-blue)](https://github.com/tryumanshow/claude-code-changelog/actions)
[![GitHub Pages](https://img.shields.io/badge/대시보드-live-green)](https://tryumanshow.github.io/claude-code-changelog)

[Anthropic Claude Code](https://github.com/anthropics/claude-code)의 전체 릴리스 히스토리를 자동 추적하는 대시보드.

**매시간** 공식 CHANGELOG.md를 파싱하여 버전별 새 커맨드, CLI 플래그, 주요 기능을 정리합니다.

> [English](README.md) | **한국어**

## Live Dashboard

**https://tryumanshow.github.io/claude-code-changelog**

- 252+ 버전 전수 조사
- 버전/커맨드/기능 실시간 검색
- "Commands only" 필터 (커맨드가 추가된 버전만 보기)
- 영어/한국어 전환 (localStorage에 저장)
- 다크 테마 + 모바일 반응형

## 동작 방식

```
GitHub Actions (매시간 cron)
  |
  v
1. anthropics/claude-code CHANGELOG.md fetch (curl)
2. GitHub Releases API + npm registry → 릴리스 날짜 수집
3. Python 파싱 → 버전, 커맨드, 기능 추출
4. OpenAI API (gpt-4o-mini) → Key Features 한국어 번역 (캐시 기반)
5. RELEASES.md (표) + docs/index.html (대시보드) 생성
6. git commit & push → GitHub Pages 자동 배포
```

## 데이터 소스

| Source | 용도 | 비고 |
|--------|------|------|
| [CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) | 버전, 커맨드, 기능 텍스트 | 매시간 fetch |
| [GitHub Releases API](https://github.com/anthropics/claude-code/releases) | 릴리스 날짜 | early-exit 캐시 |
| [npm registry](https://www.npmjs.com/package/@anthropic-ai/claude-code) | 날짜 보충 (GitHub에 없는 버전) | 캐시 200+ 시 skip |
| OpenAI API | Key Features 한국어 번역 | 번역 캐시로 재호출 최소화 |

## 프로젝트 구조

```
claude-code-changelog/
├── .github/workflows/
│   └── track-releases.yml       # GitHub Actions (매시간 cron)
├── scripts/
│   └── parse_changelog.py       # 파서 + 번역 + HTML 생성
├── data/
│   ├── releases.json            # 구조화된 전체 버전 데이터
│   ├── release_dates.json       # 날짜 캐시 (GitHub API + npm)
│   └── translations_cache.json  # 한국어 번역 캐시
├── docs/
│   └── index.html               # GitHub Pages 대시보드
├── CHANGELOG_RAW.md             # 원본 (auto-fetched)
├── RELEASES.md                  # 자동 생성 버전 표
├── README.md                    # 영어 README
└── README_ko.md                 # 한국어 README (이 파일)
```

## 설정 (Fork 후 직접 운영하기)

1. 레포 Fork
2. GitHub Pages 활성화: Settings > Pages > Source: `Deploy from a branch` > Branch: `main` / Folder: `/docs`
3. (선택) 한국어 번역: Settings > Secrets > Actions > `OPENAI_API_KEY` 추가
4. Actions 탭에서 workflow 활성화

`GITHUB_TOKEN`은 GitHub Actions가 자동 제공하므로 별도 설정 불필요.

## 커맨드 추출 로직

- **Layer 1**: 전체 changelog body에서 backtick-quoted 패턴 추출 (`` `/effort` ``, `` `--bare` ``, `` `Ctrl+B` ``)
- **Layer 2**: Unquoted 슬래시 커맨드 추출 (이전 버전에 backtick 없이 쓰인 경우)
- **Layer 3**: 59개 Known Commands 목록으로 첫 등장 버전 자동 추적
- **Blocklist**: URL 경로 (`/api`, `/docs`)와 generic 플래그 (`--no`, `--the`) 필터링

## 번역 캐시

- 한번 번역된 feature는 SHA-256 해시 기반으로 `translations_cache.json`에 저장
- 새 버전 추가 시 미번역 항목만 OpenAI API 호출 (30개씩 batch)
- 초회 약 $0.02, 이후 거의 무료

## 링크

- [Claude Code 공식 Changelog](https://code.claude.com/docs/en/changelog)
- [GitHub Releases](https://github.com/anthropics/claude-code/releases)
- [npm: @anthropic-ai/claude-code](https://www.npmjs.com/package/@anthropic-ai/claude-code)

---

<p align="center">
  Made with <a href="https://claude.ai/claude-code">Claude Code</a> by <a href="https://github.com/tryumanshow">@tryumanshow</a>
</p>
