/**
 * 공통 무한 스크롤 + Skeleton UI 유틸리티
 * 
 * 사용법:
 * const controller = createInfiniteScrollController({
 *   container: document.getElementById('grid'),
 *   loadPage: async (pageIndex, limit) => { ... },
 *   renderCard: (item) => { return cardElement; },
 *   renderSkeleton: () => { return skeletonElement; },
 *   limit: 20,
 *   sentinelId: 'sentinel-id'
 * });
 */

/**
 * 공통 Skeleton 카드 생성 (카드 스타일과 동일한 크기)
 */
function createSkeletonCard() {
  const card = document.createElement('div');
  card.className = 'skeleton-card';
  card.innerHTML = `
    <div class="skeleton-thumb"></div>
    <div class="skeleton-body">
      <div class="skeleton-name"></div>
      <div class="skeleton-meta"></div>
    </div>
  `;
  return card;
}

/**
 * Infinite Scroll Controller 생성
 */
function createInfiniteScrollController(options) {
  const {
    container,           // 그리드 컨테이너 요소
    loadPage,           // 페이지 로드 함수: async (pageIndex, limit, query) => Promise<Array>
    renderCard,         // 카드 렌더 함수: (item) => HTMLElement
    renderSkeleton,     // Skeleton 렌더 함수: () => HTMLElement
    limit = 20,         // 페이지당 아이템 수
    sentinelId,         // Sentinel 요소 ID
    rootMargin = '600px', // IntersectionObserver rootMargin
    onError = null,     // 에러 핸들러: (error) => void
  } = options;

  // 상태 관리
  let state = {
    items: [],          // 누적 아이템 배열
    pageIndex: 0,       // 현재 페이지 인덱스 (0부터 시작)
    isLoading: false,   // 로딩 중 플래그
    hasMore: true,      // 더 불러올 데이터가 있는지
    error: null,        // 에러 상태
    currentQuery: '',   // 현재 검색어
    seenIds: new Set(), // 중복 방지용 Set
    observer: null,     // IntersectionObserver 인스턴스
    sentinel: null,     // Sentinel 요소
  };

  /**
   * ID 추출 함수 (중복 방지용)
   */
  function extractId(item) {
    return item.id ?? item._id ?? item.pk ?? item.slug ?? JSON.stringify(item);
  }

  /**
   * Skeleton 카드 생성 (초기 로딩: 16개)
   */
  function renderInitialSkeletons() {
    const count = 16;
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < count; i++) {
      const skeleton = renderSkeleton();
      fragment.appendChild(skeleton);
    }
    container.appendChild(fragment);
  }

  /**
   * Skeleton 카드 생성 (추가 로딩: 4~8개)
   */
  function renderMoreSkeletons() {
    const count = Math.floor(Math.random() * 5) + 4; // 4~8개
    const fragment = document.createDocumentFragment();
    for (let i = 0; i < count; i++) {
      const skeleton = renderSkeleton();
      fragment.appendChild(skeleton);
    }
    container.appendChild(fragment);
  }

  /**
   * Skeleton 제거
   */
  function removeSkeletons() {
    const skeletons = container.querySelectorAll('.skeleton-card');
    skeletons.forEach(s => s.remove());
  }

  /**
   * Empty 상태 렌더링
   */
  function renderEmptyState(query = '') {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align:center; padding:60px 20px; color:#94a3b8;">
        <div style="font-size:16px; margin-bottom:8px;">결과 없음</div>
        <div style="font-size:13px; color:#64748b;">
          ${query ? `"${query}" 검색 결과가 없습니다.` : '표시할 항목이 없습니다.'}
        </div>
      </div>
    `;
  }

  /**
   * Error 상태 렌더링 (retry 버튼 포함)
   */
  function renderErrorState(error, retryFn) {
    const errorMessage = error?.message || '불러오기 실패';
    container.innerHTML = `
      <div style="grid-column: 1 / -1; text-align:center; padding:60px 20px; color:#ef4444;">
        <div style="font-size:16px; margin-bottom:8px;">${errorMessage}</div>
        <button 
          id="retry-btn" 
          style="margin-top:16px; padding:10px 20px; background:#3b82f6; color:#fff; border:none; border-radius:8px; cursor:pointer; font-size:14px; font-weight:500;"
        >
          다시 시도
        </button>
      </div>
    `;
    
    const retryBtn = document.getElementById('retry-btn');
    if (retryBtn && retryFn) {
      retryBtn.addEventListener('click', retryFn);
    }
  }

  /**
   * End 상태 footer 렌더링
   */
  function renderEndFooter() {
    // 기존 end footer 제거
    const existing = container.querySelector('.end-footer');
    if (existing) existing.remove();

    // 새 end footer 추가
    const footer = document.createElement('div');
    footer.className = 'end-footer';
    footer.style.cssText = 'grid-column: 1 / -1; text-align:center; padding:40px 20px; color:#64748b; font-size:13px;';
    footer.textContent = '더 이상 결과가 없습니다';
    container.appendChild(footer);
  }

  /**
   * 카드 append 렌더링
   */
  function appendCards(newItems) {
    const fragment = document.createDocumentFragment();
    newItems.forEach(item => {
      try {
        const card = renderCard(item);
        if (card) {
          fragment.appendChild(card);
        }
      } catch (err) {
        console.error('[appendCards] Error rendering card:', err, item);
      }
    });
    container.appendChild(fragment);
  }

  /**
   * 페이지 로드
   */
  async function loadPageInternal() {
    if (state.isLoading || !state.hasMore) return;

    state.isLoading = true;
    state.error = null;

    // End footer 제거
    const endFooter = container.querySelector('.end-footer');
    if (endFooter) endFooter.remove();

    try {
      // 로딩 중 Skeleton 표시 (첫 페이지가 아니면)
      if (state.pageIndex > 0) {
        renderMoreSkeletons();
      }

      // API 호출
      const items = await loadPage(state.pageIndex, limit, state.currentQuery);
      
      // Skeleton 제거
      removeSkeletons();

      if (!items || items.length === 0) {
        // 첫 페이지이고 결과가 없으면 Empty 상태
        if (state.pageIndex === 0) {
          renderEmptyState(state.currentQuery);
          state.hasMore = false;
        } else {
          // 추가 페이지이고 결과가 없으면 End
          state.hasMore = false;
          renderEndFooter();
        }
        state.isLoading = false;
        return;
      }

      // 중복 제거
      const newItems = [];
      for (const item of items) {
        const id = extractId(item);
        if (!state.seenIds.has(id)) {
          state.seenIds.add(id);
          newItems.push(item);
          state.items.push(item);
        }
      }

      // 카드 append
      if (newItems.length > 0) {
        appendCards(newItems);
      }

      // hasMore 판단: 응답 items 길이 < limit 이면 hasMore=false
      if (items.length < limit) {
        state.hasMore = false;
        renderEndFooter();
      } else {
        state.pageIndex++;
      }

    } catch (error) {
      console.error('[loadPageInternal] Error:', error);
      state.error = error;
      
      // Skeleton 제거
      removeSkeletons();

      // 에러 상태 렌더링
      if (state.pageIndex === 0) {
        renderErrorState(error, () => {
          reset();
          loadPageInternal();
        });
      } else {
        // 추가 페이지 에러: retry 버튼을 sentinel 위치에 표시
        if (state.sentinel) {
          state.sentinel.innerHTML = `
            <div style="text-align:center; padding:40px 20px; color:#ef4444;">
              <div style="font-size:14px; margin-bottom:12px;">불러오기 실패</div>
              <button 
                id="retry-next-btn"
                style="padding:8px 16px; background:#3b82f6; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:13px;"
              >
                다시 시도
              </button>
            </div>
          `;
          const retryBtn = document.getElementById('retry-next-btn');
          if (retryBtn) {
            retryBtn.addEventListener('click', () => {
              if (state.sentinel) state.sentinel.innerHTML = '';
              loadPageInternal();
            });
          }
        }
      }

      if (onError) {
        onError(error);
      }
    } finally {
      state.isLoading = false;
    }
  }

  /**
   * Sentinel 관찰 설정
   */
  function setupObserver() {
    // 기존 observer 정리
    if (state.observer) {
      state.observer.disconnect();
      state.observer = null;
    }

    // Sentinel 요소 확인/생성
    if (!state.sentinel) {
      state.sentinel = document.getElementById(sentinelId);
      if (!state.sentinel) {
        state.sentinel = document.createElement('div');
        state.sentinel.id = sentinelId;
        state.sentinel.style.cssText = 'height:1px; min-height:1px;';
        container.after(state.sentinel);
      }
    }

    // IntersectionObserver 생성
    state.observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && state.hasMore && !state.isLoading) {
            loadPageInternal();
          }
        }
      },
      { root: null, rootMargin: rootMargin, threshold: 0 }
    );

    state.observer.observe(state.sentinel);
  }

  /**
   * 초기화 (첫 페이지 로드)
   */
  async function init(query = '') {
    reset(query);
    
    // 초기 Skeleton 표시
    renderInitialSkeletons();
    
    // 첫 페이지 로드
    await loadPageInternal();
    
    // Observer 설정
    setupObserver();
  }

  /**
   * 리셋 (검색어 변경, 탭 전환 등)
   */
  function reset(query = '') {
    // 상태 초기화
    state.items = [];
    state.pageIndex = 0;
    state.isLoading = false;
    state.hasMore = true;
    state.error = null;
    state.currentQuery = query;
    state.seenIds.clear();

    // Observer 정리
    if (state.observer) {
      state.observer.disconnect();
      state.observer = null;
    }

    // Sentinel 정리 (제거하지 않고 내용만 비움)
    if (state.sentinel) {
      state.sentinel.innerHTML = '';
    }

    // 컨테이너 비우기
    container.innerHTML = '';
  }

  /**
   * 수동으로 다음 페이지 로드 (필요시)
   */
  async function loadNext() {
    await loadPageInternal();
  }

  /**
   * 현재 상태 반환
   */
  function getState() {
    return {
      items: [...state.items],
      pageIndex: state.pageIndex,
      isLoading: state.isLoading,
      hasMore: state.hasMore,
      error: state.error,
      currentQuery: state.currentQuery,
    };
  }

  /**
   * 정리 (컴포넌트 unmount 시)
   */
  function cleanup() {
    if (state.observer) {
      state.observer.disconnect();
      state.observer = null;
    }
    // Sentinel은 제거하지 않음 (나중에 재사용 가능)
  }

  return {
    init,
    reset,
    loadNext,
    getState,
    cleanup,
  };
}
