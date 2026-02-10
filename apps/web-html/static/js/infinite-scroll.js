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
    root = null,         // IntersectionObserver root (null=window, 요소=해당 요소 스크롤)
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
    sentinelId: sentinelId, // Sentinel ID 저장 (컨테이너 비우기 시 보존용)
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
    // 디버그 로그: append 전후 childCount 확인
    const beforeCount = container?.children?.length || 0;
    console.log('[DBG infinite-scroll] appendCards: before append childCount=', beforeCount, 'newItems.len=', newItems?.length);
    
    const fragment = document.createDocumentFragment();
    let appendedCount = 0;
    newItems.forEach(item => {
      try {
        const card = renderCard(item);
        if (card) {
          fragment.appendChild(card);
          appendedCount++;
        } else {
          console.warn('[DBG infinite-scroll] appendCards: renderCard returned null/undefined for item:', item);
        }
      } catch (err) {
        console.error('[DBG infinite-scroll] appendCards: Error rendering card:', err, item);
      }
    });
    container.appendChild(fragment);
    
    // 중요: 카드가 추가된 뒤 sentinel을 항상 맨 아래로 이동
    // appendChild는 이미 자식인 노드를 맨 뒤로 이동시켜줌
    if (state.sentinel && container.contains(state.sentinel)) {
      container.appendChild(state.sentinel);
    }
    
    // 디버그 로그: append 후 실제 DOM 증가 확인
    const afterCount = container?.children?.length || 0;
    console.log('[inf] after append childCount=', afterCount, 'sentinelAtEnd=', container.lastElementChild?.id);
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
      
      // 디버그 로그
      console.log('[DBG infinite-scroll] loadPageInternal items.len=', items?.length, 'pageIndex=', state.pageIndex);
      
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

      // 중복 제거 전 로그
      console.log('[inf] pageIndex=', state.pageIndex, 'incoming=', items.length);
      
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

      // 중복 제거 후 로그
      console.log('[inf] deduped=', newItems.length);
      if (items.length && newItems.length === 0) {
        console.log('[inf] DUP_ALL sample ids=', items.slice(0, 5).map(x => x.id || x._id || x.pk || x.slug || 'undefined'));
      }

      // 카드 append
      if (newItems.length > 0) {
        console.log('[DBG infinite-scroll] loadPageInternal: calling appendCards with', newItems.length, 'items, pageIndex=', state.pageIndex, 'hasMore=', state.hasMore);
        appendCards(newItems);
      } else {
        console.warn('[DBG infinite-scroll] loadPageInternal: No new items after deduplication, items.len=', items.length, 'seenIds.size=', state.seenIds.size);
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

    // Sentinel 요소 확인/생성/재부착 (반드시 보장)
    if (!state.sentinel) {
      // 1. 먼저 DOM에서 전역으로 찾기
      state.sentinel = document.getElementById(sentinelId);
      
      // 2. 없으면 container 내부에서 찾기
      if (!state.sentinel && container) {
        state.sentinel = container.querySelector(`#${sentinelId}`);
      }
      
      // 3. 그래도 없으면 새로 생성
      if (!state.sentinel) {
        state.sentinel = document.createElement('div');
        state.sentinel.id = sentinelId;
        state.sentinel.style.cssText = 'height:1px; min-height:1px;';
      }
      
      // 4. sentinel을 올바른 위치에 재부착 (root 여부에 따라)
      if (root) {
        // 모달 내부 스크롤: container 내부에, 무조건 맨 아래로 이동
        if (!container.contains(state.sentinel)) {
          container.appendChild(state.sentinel);
        } else {
          // 이미 container 안에 있어도 맨 아래로 이동 (appendChild는 자식 노드를 맨 뒤로 이동시킴)
          container.appendChild(state.sentinel);
        }
      } else {
        // 전체 스크롤: container 뒤에
        if (state.sentinel.parentNode !== container.parentNode || 
            state.sentinel.previousSibling !== container) {
          container.after(state.sentinel);
        }
      }
      
      // 디버그 로그
      console.log('[DBG infinite-scroll] setupObserver sentinel:', {
        exists: !!state.sentinel,
        inContainer: container.contains(state.sentinel),
        sentinelId: sentinelId
      });
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
      { root: root, rootMargin: rootMargin, threshold: 0 }
    );

    state.observer.observe(state.sentinel);
  }

  /**
   * 컨테이너 비우기 (sentinel 보존)
   */
  function clearContainerKeepSentinel() {
    const sentinel = state.sentinelId ? document.getElementById(state.sentinelId) : null;
    
    // container 내 child를 전부 제거하되, sentinel만 남긴다
    Array.from(container.children).forEach(ch => {
      if (!sentinel || ch !== sentinel) {
        container.removeChild(ch);
      }
    });
    
    // sentinel이 있으면 맨 아래로 이동(=마지막 보장)
    if (sentinel) {
      container.appendChild(sentinel);
    }
  }

  /**
   * 초기화 (첫 페이지 로드)
   */
  async function init(query = '') {
    reset(query);
    
    // 기존 카드/Skeleton 제거 (reset 후에만 수행)
    // sentinel은 보존하여 DOM 생명주기를 끊지 않음
    clearContainerKeepSentinel();
    
    // 초기 Skeleton 표시
    renderInitialSkeletons();
    
    // 첫 페이지 로드
    await loadPageInternal();
    
    // Observer 설정 (sentinel 재탐색/재생성/재부착 보장)
    setupObserver();
  }

  /**
   * 리셋 (검색어 변경, 탭 전환 등)
   * DOM을 직접 조작하지 않고 상태만 초기화 (sentinel 보존)
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

    // Sentinel 참조 초기화 (다음 setupObserver에서 다시 찾음)
    // DOM에서 제거하지 않음 - setupObserver()에서 재탐색/재부착 보장
    state.sentinel = null;

    // 중요: container.innerHTML = '' 같은 DOM 직접 삭제는 하지 않음
    // 필요시 init() 내부의 renderInitialSkeletons() 전에 기존 카드들을 제거하거나,
    // onReset 콜백에서 처리하도록 함
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
